# Pokémon 30th Celebration restock/listing alert

Watches Australian retailers and pings a Discord channel the moment
something relevant happens. Two kinds of watch, both in `config.json`:

- **`listing_watches`** — watches a category/search page for product
  links matching a keyword (e.g. "30th Celebration"), alerts once when a
  NEW one appears, and then keeps following every matching link it's
  found so far to check its own stock status too — so it also alerts on
  restocks, not just first sightings. Good for a retailer you don't have
  a direct product URL for yet.
- **`stock_watches`** — watches one specific product page directly and
  alerts every time it flips from unavailable to in-stock (including
  after multiple sell-out/restock cycles).

Both watch types catch a restock, not just an initial listing — that
was a gap in an earlier version of this tool (listing_watches used to
go quiet after the first sighting) and is now fixed.

It only sends you a notification — it never adds anything to a cart or
checks out for you.

## Important: this set already released

The set is officially called **Pokémon TCG: 30th Celebration**, and it
released worldwide on **16 September 2026** — the day this was built.
Product pages were already live (and, under launch-day load, flickering
in and out with 404s and server errors) at several retailers. That
flakiness is completely normal for a hyped drop's first day and is
exactly the situation this tool is built to sit and watch for you — it
isn't a sign the config is broken.

## Retailers covered (21 total)

**Mainstream / big-box** (`config.json` already has confirmed real
30th Celebration product URLs for these as `stock_watches`, since pages
already existed when this was built):

- Big W, Kmart, EB Games, JB Hi-Fi, Toymate

**Mainstream, listing-watch only** (category page watched now; add a
`stock_watch` once you spot a direct product URL):

- Target Australia, Mr Toys, Toyworld, Amazon Australia, Toys "R" Us
  Australia (relaunched online-only in 2026 via Hobby Warehouse)

**Official store**:

- Pokémon Center Australia (`pokemoncenter.com/en-au`) — this now
  exists and ships to Australia. Its 30th Celebration category page was
  stuck on a loading/queue screen when this was tested (also normal for
  launch-day Pokémon Center traffic), so it's set up as a listing-watch
  for now.

**Specialty/hobby "drop store" retailers** — these are smaller AU-based
TCG-focused shops that often get separate allocations from the big
chains and tend to restock faster, though they can price above RRP:

- Grailborne, Drop Store, Collectible Madness, Gameology, Trainer Town,
  Kidstuff, Good Games, PokeSource AU, Unplugged Games, Milsims Games,
  Games World — all confirmed carrying 30th Celebration stock or
  listings; several (Grailborne) were already showing "Sold Out" within
  hours of release, which tells you how fast this set is moving.

**Not included, but worth knowing about**: Card Traders Australia
(social-media presence confirmed, but no working store URL was found to
watch) and Overhauled Games in Melbourne (a real TCG store, but no
30th Celebration listing was confirmed for it specifically). There's
also **CardWatch AU** (cardwatch.com.au) — an existing Australian site
that already tracks this exact set's stock across retailers, including
a release-day guide, worth bookmarking as a second opinion alongside
your own alerts.

## 1. Create a Discord webhook (2 minutes)

1. Open Discord and pick (or create) the server you want alerts posted
   in. To create one: click the **+** at the bottom of the server list
   → **Create My Own** → **For me and my friends** → give it any name.
2. Pick a text channel for alerts, or make a new one (click the **+**
   next to **TEXT CHANNELS** in that server, name it e.g.
   `pokemon-restock`).
3. Hover over the channel name and click the **gear/settings icon**
   that appears (or right-click the channel → **Edit Channel**).
4. In the panel that opens, click **Integrations** in the left-hand
   list, then **Webhooks**, then **New Webhook** (or **Create
   Webhook**).
5. A webhook named something like "Captain Hook" appears. Click it,
   rename it to something recognisable like "Pokémon Alerts", and
   click **Copy Webhook URL**. It looks like
   `https://discord.com/api/webhooks/1234567890/AbCdEfG...`.
6. Click **Save Changes**. Paste that URL somewhere temporary (a notes
   app) — you'll need it in step 3 below. Keep it private: anyone with
   this URL can post messages into that channel.

## 2. Unzip the project and check the files

Unzip `pokemon-restock-alert.zip`. You should see `check_stock.py`,
`config.json`, `requirements.txt`, `README.md`, `state.json`, and a
**`.github`** folder containing `workflows/check-stock.yml`.

That `.github` folder is easy to miss because folders starting with a
dot are hidden by default on most systems. Before continuing, make sure
your file manager is showing it:

- **Mac (Finder)**: press `Cmd+Shift+.` (period) to toggle hidden files.
- **Windows (File Explorer)**: View tab → tick **Hidden items**.

If you can't see `.github/workflows/check-stock.yml` in the unzipped
folder, the upload in the next step will silently miss the one file
that actually makes the automation run.

## 3. Create the GitHub repository (3 minutes)

1. Go to [github.com](https://github.com) and sign in (or create a free
   account if you don't have one already — that part's on you, this
   isn't something I can do for you).
2. Click the **+** icon in the top-right corner → **New repository**.
3. Give it a name, e.g. `pokemon-restock-alert`.
4. Set visibility to **Public** — public repos get unlimited free
   GitHub Actions minutes; private repos have a monthly cap that a
   5-minute schedule will burn through in a few days. Nothing sensitive
   lives in this code either way — the only secret (the webhook URL) is
   stored separately in step 5, never in a file.
5. Leave **"Add a README file"** unticked, so the repo starts empty and
   shows an upload prompt immediately.
6. Click **Create repository**.

## 4. Upload the files (2 minutes)

1. On the new, empty repo page, click **uploading an existing file**
   (the link in the "Get started" text).
2. Open the unzipped `pokemon-restock-alert` folder in your file
   manager so you can see its *contents* (`check_stock.py`,
   `config.json`, the `.github` folder, etc.) — not the parent folder
   itself.
3. Select everything inside it (`Ctrl+A` / `Cmd+A`) and drag the whole
   selection onto GitHub's upload area at once.
4. Watch the list of files GitHub builds as it processes the drop, and
   confirm `.github/workflows/check-stock.yml` shows up in it. If it
   doesn't, your file manager was still hiding it — go back, reveal
   hidden files, and drag again.
5. Scroll down to **Commit changes**, leave the default message (or
   write "Initial commit"), make sure **Commit directly to the main
   branch** is selected, and click **Commit changes**.
6. You should land back on the repo's file listing, now showing your
   files including a `.github` folder.

## 5. Add the Discord webhook as a secret (1 minute)

1. In the repo, click the **Settings** tab (top of the page).
2. In the left sidebar, click **Secrets and variables** → **Actions**.
3. Click the green **New repository secret** button.
4. Name: type exactly `DISCORD_WEBHOOK_URL` — this has to match the
   code exactly, it's case-sensitive.
5. Secret: paste the webhook URL you copied from Discord in step 1.
6. Click **Add secret**. You should now see `DISCORD_WEBHOOK_URL`
   listed under Repository secrets (its value stays hidden).

## 6. Enable and test the workflow (2 minutes)

1. Click the **Actions** tab at the top of the repo.
2. If GitHub shows any banner about enabling workflows for this repo,
   click through it to allow them.
3. In the left sidebar under "All workflows", click **Check Pokemon
   restock/listing alerts**.
4. On the right, click the **Run workflow** dropdown, then the green
   **Run workflow** button inside it (leave the branch as `main`).
5. Wait a few seconds and refresh the page. A new run appears with a
   yellow dot (in progress); it turns into a green checkmark (success)
   or a red X (failed) once it finishes — usually well under a minute.
6. Click into that run → the **check** job → expand **Run stock/listing
   check** to see the live log. You should see lines like `[Kmart -
   30th Celebration Elite Trainer Box] Status: OUT_OF_STOCK` and a
   final `Run finished in X.Xs` line.
7. Check Discord: you likely won't get a message on this very first run
   unless something happens to be newly in stock right now — silence
   here is expected and means it's working, not that it's broken.
8. If the run shows a red X, open the failed step to read the error.
   The most common cause is the secret name being slightly wrong; if
   the workflow doesn't even appear in step 6.3 at all, that means the
   `.github` folder didn't upload in step 4 — go back and re-check that.

That's it — from here it runs automatically every 5 minutes, forever,
for free, without your computer needing to be on. Come back to the
Actions tab in 15–20 minutes and you should see more runs appear on
their own, marked as triggered by "schedule" rather than by you — that
confirms the automatic schedule is working, not just your manual test.

## 7. Adding more products or retailers

Copy the template entry at the bottom of `stock_watches` in
`config.json`, fill in the real product URL, and set `retailer` to
whichever key in `RETAILER_RULES` (top of `check_stock.py`) matches that
site's platform:

```json
{
  "enabled": true,
  "name": "30th Celebration Elite Trainer Box - Some Store",
  "retailer": "shopify_generic",
  "url": "https://example.com/products/replace-me"
}
```

`shopify_generic` covers most small AU card/hobby stores (anything with
`/products/` and `/collections/` in its URLs). Commit and push — no
other code changes needed.

## Notes and limitations

- **Run time and concurrency**: since listing_watches also check the
  stock of every matching product they find, a run does a lot of page
  loads in total (40+ watches, some pulling in extra product pages).
  To keep the 5-minute schedule realistic, checks run concurrently
  rather than one at a time - `CONCURRENCY_LIMIT` in `check_stock.py`
  (default 6) caps how many page loads are in flight at once. The log
  prints a "Run finished in Xs" line at the end of every run - keep an
  eye on that in the Actions tab. If runs are creeping past a few
  minutes as you add more watches, you can raise `CONCURRENCY_LIMIT`
  (faster, but more simultaneous load on the target sites and the
  runner), trim `MAX_PRODUCT_CHECKS_PER_LISTING`, or split the watches
  across two workflow files on staggered schedules.
- **Speed**: GitHub's schedule is every 5 minutes and isn't perfectly
  exact (it can lag a few minutes during peak load). That's the
  practical ceiling for a free, no-server setup. If you want
  faster/near-instant checks, the next step up is moving the same logic
  to a Cloudflare Workers Cron Trigger (free tier allows 1-minute
  schedules) — ask if you want that built out.
- **Target Australia and Amazon Australia** were both flaky/heavily
  bot-protected when this was built — Target threw JavaScript errors on
  some real product pages, and Amazon is known for CAPTCHA-gating
  headless browsers. Both are wired up as listing-watches only for now,
  and an unreadable page is treated as "unknown" (never alerted, never
  overwrites the last known status) rather than guessed at.
- **Unverified phrase lists**: Toymate, Mr Toys, Toyworld, Pokémon
  Center Australia, Amazon, Milsims Games and Games World's exact "in
  stock"/"out of stock" wording wasn't confirmed live (their pages were
  erroring, queued, bot-gated, or just not spot-checked at build time)
  — their entries in `RETAILER_RULES` are reasonable defaults for the
  platform each site looks like it runs. Watch your Discord channel for
  the first alert from each and sanity check it against the real page;
  adjust the phrase lists if needed.
- **The Big W "Marketplace" listing**: the ETB Pre-Sale URL from Big W
  in `config.json` is sold by a third-party marketplace seller, not
  Big W itself, and was priced with an inflated "SAVE $300" badge —
  common for reseller listings during a hyped drop. It's included
  because it's a real, currently-live listing, but treat its price with
  more skepticism than a "Sold & shipped by Big W" listing.
- **Sites blocking the runner's IP**: GitHub Actions runners use
  well-known shared IP ranges, and heavily bot-protected sites (Amazon,
  Target, anything behind Cloudflare/Akamai) sometimes start silently
  blocking or CAPTCHA-gating that traffic over time, unrelated to
  anything being wrong with the config. If a retailer that used to work
  starts reporting UNKNOWN on every run, this is the likely cause.
- **Discord rate limits**: Discord caps a webhook at roughly 30
  messages/minute. If a lot of products flip status in the same run
  (e.g. right at a midnight launch), later alerts in that burst could
  get silently rate-limited rather than delivered - the script doesn't
  currently retry on a 429.
- **Long-term dormancy**: GitHub auto-disables a scheduled workflow
  after 60 days with no repository activity, and this workflow only
  commits when `state.json` actually changes. Not a near-term concern
  given how fast this set is already moving, but if you keep this
  running for months after things quiet down, check the Actions tab
  occasionally to make sure it's still firing.
- **This is a notify-only tool, by design**: it never adds to cart or
  checks out automatically, and that's intentional, not a missing
  feature - an auto-purchasing version would cross into scalping-bot
  territory that competes unfairly with other shoppers.
- State (what's already been seen/alerted) lives in `state.json`, which
  the workflow commits back to the repo after every run — that's how it
  avoids re-alerting you for the same thing every 5 minutes.
