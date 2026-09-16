#!/usr/bin/env python3
"""
Restock / new-listing alert checker for Australian retailers.

Two modes, both configured in config.json:

  listing_watches  - watches a category/search page for product links
                      matching one of `keywords`. Alerts once when a NEW
                      link appears, and keeps checking every matching
                      link's own stock status on every run afterwards too
                      (so it also catches restocks, not just first
                      sightings).

  stock_watches    - watches one specific product page directly and
                      alerts every time it flips from "not orderable" to
                      "in stock".

State (what we've already seen / alerted on) is kept in a state JSON
file (state.json by default, or whatever --state points at) so we only
ever alert on a *change*, never on every run.

Notifications go to a Discord channel via a webhook URL, read from the
DISCORD_WEBHOOK_URL environment variable (set as a GitHub Actions secret;
see README.md).

Checks run concurrently (bounded by CONCURRENCY_LIMIT) rather than one
page load at a time, so a run finishes in roughly
(total page loads / CONCURRENCY_LIMIT) time instead of the full serial
sum.

Config/state files are configurable via --config/--state (see
`python check_stock.py --help`), which is what lets multiple copies of
this same script run in parallel as separate GitHub Actions matrix
jobs, each one only responsible for a slice of retailers (see
config/shard-*.json and the "sharded" workflow in
.github/workflows/check-stock.yml) - each shard gets its own state
file too, so parallel jobs never write-conflict with each other.
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path
from urllib.parse import urljoin
import urllib.request
import urllib.error

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

# How long to let a page settle after load before reading it. These sites
# are all JS-rendered (React/Next.js) so the real content isn't in the raw
# HTML - a headless browser is required, not a plain HTTP GET.
PAGE_TIMEOUT_MS = 30_000
SETTLE_SECONDS = 2.5

# How many page loads (category pages, product pages, everything) are
# allowed to be in flight at once, across the whole run. Higher = faster
# runs, but more simultaneous load on the target sites and on the runner.
# 6 is a reasonable middle ground - fast enough to keep a 5-minute cron
# schedule realistic even with 40+ watches, without hammering any one
# retailer with a big simultaneous burst.
CONCURRENCY_LIMIT = 6

# How many matching product pages a single listing_watch will follow and
# check stock on, per run (also bounded by CONCURRENCY_LIMIT overall). A
# "30th anniversary" filter on a category page realistically matches a
# handful of products, not hundreds, so this should rarely be hit.
MAX_PRODUCT_CHECKS_PER_LISTING = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

# Per-retailer phrases used to classify a product page's stock status.
# These were confirmed by loading real product pages on each site:
#   - Big W out-of-stock/discontinued items 404 to a "Page Not Found" page
#     with this exact copy; in-stock items show "Add to cart".
#   - Kmart shows the literal word "Out of stock" when unavailable, and
#     "Add to bag" when available.
#   - JB Hi-Fi and EB Games show "Add to cart" when available; "Sold Out"
#     / "Notify me" are the common out-of-stock patterns on both platforms.
#   - Target Australia's product pages were unstable at the time this was
#     written (client-side JS errors on some loads even for real,
#     in-stock products) - treated conservatively, see classify_stock().
#   - Zing Pop Culture runs the same storefront platform as EB Games (same
#     URL/markup conventions), so it reuses those phrases.
#   - Grailborne, Drop Store, Collectible Madness, Gameology and Trainer
#     Town are all Shopify storefronts (confirmed by their /products/ and
#     /collections/ URLs) and share Shopify's default wording: "Sold Out"
#     replaces the buy button when unavailable, "Add to cart" otherwise.
#     Give any of these (or another Shopify-based AU card store) the
#     retailer key "shopify_generic".
#   - toymate, mrtoys, toyworld, pokemoncenter, amazon, milsims and
#     gamesworld were NOT live long enough at build time to confirm their
#     exact wording (Toymate 500'd under launch-day load, Pokémon Center
#     AU was stuck on a loading/queue screen, Target and Amazon are both
#     known for heavy bot-detection). Their phrase lists below are
#     reasonable defaults for the e-commerce platform each one looks like
#     it runs, not confirmed live text - check the first alert (or lack
#     of one) against the real page and adjust here if needed. Amazon in
#     particular may just fail to render at all under a headless browser
#     without a logged-in session; treat it as best-effort.
RETAILER_RULES = {
    "bigw": {
        "out_of_stock_phrases": [
            "page not found",
            "temporarily out of stock or discontinued",
        ],
        "in_stock_phrases": ["add to cart"],
    },
    "kmart": {
        "out_of_stock_phrases": ["out of stock"],
        "in_stock_phrases": ["add to bag"],
    },
    "target": {
        "out_of_stock_phrases": ["out of stock", "sold out", "unavailable"],
        "in_stock_phrases": ["add to cart"],
    },
    "jbhifi": {
        "out_of_stock_phrases": ["sold out", "notify me"],
        "in_stock_phrases": ["add to cart"],
    },
    "ebgames": {
        "out_of_stock_phrases": ["out of stock", "notify me when available"],
        "in_stock_phrases": ["add to cart"],
    },
    "zing": {
        "out_of_stock_phrases": ["out of stock", "notify me when available"],
        "in_stock_phrases": ["add to cart"],
    },
    "shopify_generic": {
        "out_of_stock_phrases": ["sold out"],
        "in_stock_phrases": ["add to cart"],
    },
    "toymate": {
        "out_of_stock_phrases": ["out of stock"],
        "in_stock_phrases": ["add to cart"],
    },
    "mrtoys": {
        "out_of_stock_phrases": ["out of stock", "notify me", "temporarily unavailable"],
        "in_stock_phrases": ["add to cart"],
    },
    "toyworld": {
        "out_of_stock_phrases": ["out of stock", "sold out"],
        "in_stock_phrases": ["add to cart"],
    },
    "milsims": {
        "out_of_stock_phrases": ["out of stock", "sold out", "notify me"],
        "in_stock_phrases": ["add to cart"],
    },
    "gamesworld": {
        "out_of_stock_phrases": ["out of stock", "read more"],
        "in_stock_phrases": ["add to cart"],
    },
    "pokemoncenter": {
        "out_of_stock_phrases": ["out of stock", "notify me", "sold out"],
        "in_stock_phrases": ["add to cart", "add to bag"],
    },
    "amazon": {
        "out_of_stock_phrases": ["currently unavailable", "out of stock"],
        "in_stock_phrases": ["add to cart"],
    },
}

IN_STOCK = "IN_STOCK"
OUT_OF_STOCK = "OUT_OF_STOCK"
UNKNOWN = "UNKNOWN"


def log(msg: str, tag: str = "") -> None:
    prefix = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]"
    if tag:
        prefix += f" [{tag}]"
    print(f"{prefix} {msg}", flush=True)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        log(f"WARNING: {path} was not valid JSON, ignoring it.")
        return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def send_discord_alert(message: str) -> bool:
    """Blocking - call via `await asyncio.to_thread(send_discord_alert, ...)`
    from async code so it doesn't stall the event loop mid-run. Returns
    True only if Discord actually accepted the message - callers must
    check this rather than assuming a POST attempt means delivery."""
    if not DISCORD_WEBHOOK_URL:
        log("No DISCORD_WEBHOOK_URL set - printing alert instead of sending it:")
        log(message)
        return False
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            # Discord sits behind Cloudflare, which can 403 (error 1010)
            # requests carrying urllib's default "Python-urllib/x.y"
            # user-agent as a bot fingerprint. A normal browser-looking
            # UA avoids that block.
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
            return True
    except urllib.error.HTTPError as e:
        log(f"Discord webhook failed: HTTP {e.code} {e.read()[:300]}")
        return False
    except Exception as e:  # noqa: BLE001 - never let a notify failure kill the run
        log(f"Discord webhook failed: {e}")
        return False


async def alert(message: str) -> bool:
    return await asyncio.to_thread(send_discord_alert, message)


async def render_page(context, semaphore: asyncio.Semaphore, url: str) -> str:
    """Load `url` in a fresh page (bounded by `semaphore`) and return the
    fully rendered HTML after client-side JS has run. Each call gets its
    own Page so many of these can be in flight concurrently."""
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
            await page.wait_for_timeout(int(SETTLE_SECONDS * 1000))
            return await page.content()
        finally:
            await page.close()


def classify_stock(retailer: str, html: str) -> str:
    rules = RETAILER_RULES.get(retailer)
    if not rules:
        log(f"WARNING: no rules for retailer '{retailer}', treating as UNKNOWN.")
        return UNKNOWN

    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True).lower()

    if any(p in text for p in rules["out_of_stock_phrases"]):
        return OUT_OF_STOCK
    if any(p in text for p in rules["in_stock_phrases"]):
        return IN_STOCK
    return UNKNOWN


def find_matching_links(html: str, base_url: str, keywords: list[str]) -> dict[str, str]:
    """Return {absolute_url: link_text} for every <a> on the page whose
    visible text contains one of `keywords` (case-insensitive)."""
    soup = BeautifulSoup(html, "html.parser")
    keywords_lower = [k.lower() for k in keywords]
    matches: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        if not text:
            continue
        low = text.lower()
        if any(k in low for k in keywords_lower):
            abs_url = urljoin(base_url, a["href"])
            matches[abs_url] = text
    return matches


async def check_one_product(context, semaphore, retailer: str, url: str) -> str:
    """Load one product page and classify its stock status. Never raises -
    returns UNKNOWN on any failure so one bad page can't sink a whole run."""
    try:
        html = await render_page(context, semaphore, url)
        return classify_stock(retailer, html)
    except Exception as e:  # noqa: BLE001
        log(f"Failed to check {url}: {e}")
        return UNKNOWN


async def run_listing_watch(context, semaphore, entry: dict, state: dict) -> None:
    """Watch a category/search page for matching product links, AND keep
    checking the stock status of every matching link found - so a listing
    that's discovered once keeps getting monitored for restocks too,
    instead of going silent after the first sighting."""
    name = entry["name"]
    url = entry["url"]
    retailer = entry.get("retailer", "unknown")
    keywords = entry.get("keywords", [])
    key = f"listing::{url}"
    tag = name

    log(f"Checking listing watch ({url})", tag)
    try:
        html = await render_page(context, semaphore, url)
    except Exception as e:  # noqa: BLE001
        log(f"Failed to load category page: {e}", tag)
        return

    matches = find_matching_links(html, url, keywords)
    prior_state = state.get(key, {})
    seen_before = set(prior_state.get("seen_urls", []))
    product_status = dict(prior_state.get("product_status", {}))  # url -> status
    new_urls = {u for u in matches if u not in seen_before}

    to_check = list(matches.items())[:MAX_PRODUCT_CHECKS_PER_LISTING]
    statuses = await asyncio.gather(
        *(check_one_product(context, semaphore, retailer, u) for u, _ in to_check)
    )

    new_listing_lines = []
    restock_lines = []

    for (u, link_text), status in zip(to_check, statuses):
        previous = product_status.get(u, UNKNOWN)
        if status != UNKNOWN:
            product_status[u] = status

        if u in new_urls:
            status_label = {
                IN_STOCK: "IN STOCK",
                OUT_OF_STOCK: "not in stock yet",
                UNKNOWN: "stock status unclear",
            }[status]
            new_listing_lines.append(f"• {link_text} ({status_label})\n  {u}")
        elif status == IN_STOCK and previous != IN_STOCK:
            restock_lines.append(f"• {link_text}\n  {u}")

    if new_listing_lines:
        delivered = await alert(
            "\n".join([f"🆕 **New listing spotted at {retailer.upper()}** — {name}"] + new_listing_lines)
        )
        if delivered:
            log(f"ALERT sent: {len(new_listing_lines)} new matching link(s).", tag)
        else:
            log(f"ALERT DELIVERY FAILED (see Discord webhook error above): "
                f"{len(new_listing_lines)} new matching link(s) not delivered to Discord.", tag)
    if restock_lines:
        delivered = await alert(
            "\n".join([f"🚨 **Back in stock at {retailer.upper()}** — {name}"] + restock_lines)
        )
        if delivered:
            log(f"ALERT sent: {len(restock_lines)} link(s) back in stock.", tag)
        else:
            log(f"ALERT DELIVERY FAILED (see Discord webhook error above): "
                f"{len(restock_lines)} link(s) back in stock not delivered to Discord.", tag)
    if not new_listing_lines and not restock_lines:
        log(f"No change ({len(matches)} matching link(s), none newly listed or newly in stock).", tag)

    state[key] = {
        "type": "listing_watch",
        "name": name,
        "seen_urls": sorted(seen_before | set(matches.keys())),
        "product_status": product_status,
    }


async def run_stock_watch(context, semaphore, entry: dict, state: dict) -> None:
    if not entry.get("enabled", True):
        return

    name = entry["name"]
    url = entry["url"]
    retailer = entry.get("retailer", "unknown")
    key = f"stock::{url}"
    tag = name

    log(f"Checking stock watch ({url})", tag)
    try:
        html = await render_page(context, semaphore, url)
    except Exception as e:  # noqa: BLE001
        log(f"Failed to load page: {e}", tag)
        return

    status = classify_stock(retailer, html)
    previous = state.get(key, {}).get("status", UNKNOWN)

    if status == UNKNOWN:
        # Don't let a flaky/slow render overwrite a known good status or
        # fire a false alert - just log it and move on.
        log(f"Status UNKNOWN (previous recorded status: {previous}); leaving state unchanged.", tag)
        return

    log(f"Status: {status} (previous: {previous})", tag)

    if status == IN_STOCK and previous != IN_STOCK:
        delivered = await alert(f"🚨 **IN STOCK** — {name} ({retailer.upper()})\n{url}")
        if delivered:
            log("ALERT sent: now in stock.", tag)
        else:
            log("ALERT DELIVERY FAILED (see Discord webhook error above): now in stock but not delivered to Discord.", tag)

    state[key] = {"type": "stock_watch", "name": name, "status": status}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to the config JSON file to read watches from (default: config.json). "
             "Relative paths are resolved from the script's own directory.",
    )
    parser.add_argument(
        "--state",
        default="state.json",
        help="Path to the state JSON file to read/write (default: state.json). "
             "Give each parallel/sharded invocation its own state file so they "
             "never overwrite each other.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    config_path = ROOT / args.config
    state_path = ROOT / args.state

    config = load_json(config_path, {})
    state = load_json(state_path, {})

    listing_watches = config.get("listing_watches", [])
    stock_watches = [w for w in config.get("stock_watches", []) if w.get("enabled")]

    if not listing_watches and not stock_watches:
        log(f"No enabled watches in {config_path.name} - nothing to do.")
        return 0

    start = time.monotonic()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=USER_AGENT, locale="en-AU")
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        tasks = [run_listing_watch(context, semaphore, entry, state) for entry in listing_watches]
        tasks += [run_stock_watch(context, semaphore, entry, state) for entry in stock_watches]
        # Shuffle so the first wave through the concurrency limit isn't
        # weighted toward whichever retailer happens to be listed first in
        # config.json (keeps simultaneous hits spread across retailers).
        random.shuffle(tasks)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                log(f"A watch task raised an unhandled error: {r}")

        await browser.close()

    elapsed = time.monotonic() - start
    log(f"Run finished in {elapsed:.1f}s across {len(listing_watches)} listing watch(es) "
        f"and {len(stock_watches)} stock watch(es) (concurrency={CONCURRENCY_LIMIT}, "
        f"config={config_path.name}, state={state_path.name}).")

    save_json(state_path, state)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
