# Pokémon 30th Celebration restock/listing alert

Watches Australian retailers and pings a Discord channel the moment
something relevant happens. Two kinds of watch, both configured in the
`config/shard-*.json` files (see "How checking is split across shards"
below for why there are 6 of these instead of one `config.json`):

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

**Mainstream / big-box** (the config already has confirmed real
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
`requirements.txt`, `README.md`, a **`config`** folder (containing
`shard-1.json` through `shard-6.json`), a **`state`** folder (containing
matching empty `shard-1.json` through `shard-6.json` files), and a
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
   manager so you can see its *contents* (`check_stock.py`, the
   `config` folder, the `.github` folder, etc.) — not the parent
   folder itself.
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
5. Wait a few seconds and refresh the page. This time **6 runs appear
   at once** — `check (1)` through `check (6)` — one per shard, all
   running in parallel. Each shows its own yellow dot (in progress)
   that turns into a green checkmark (success) or red X (failed).
6. Click into any one of the 6 → expand **Run checks continuously for
   this shard** to see its live log. You should see lines like
   `[Kmart - 30th Celebration Elite Trainer Box] Status: OUT_OF_STOCK`,
   a `Run finished in X.Xs` line, then `=== Shard N, cycle 2 ===` and
   it starts again. Each shard step deliberately keeps running for
   hours (see "How the continuous cycling works" below) — the run
   staying "in progress" with a yellow dot for a long time is
   expected, not stuck.
7. Check Discord: you likely won't get a message on the first cycle or
   two unless something happens to be newly in stock right now —
   silence here is expected and means it's working, not that it's
   broken.
8. If any of the 6 shows a red X, open its failed step to read the
   error. The most common cause is the secret name being slightly
   wrong (this would affect all 6 the same way, since they share the
   one secret); if the workflow doesn't even appear in step 6.3 at
   all, that means the `.github` folder didn't upload in step 4 — go
   back and re-check that.

That's it — from here it checks continuously, forever, for free,
without your computer needing to be on. See the next section for how
that actually works under the hood.

## How checking is split across shards

Rather than one job checking all 40+ watches, the workflow uses a
GitHub Actions **matrix** to run 6 separate jobs in parallel, each on
its own runner, each responsible for a slice of retailers defined in
`config/shard-1.json` through `config/shard-6.json` (see
`config/README.md` for exactly which stores are in which shard, and
how to add a new watch). This is mainly a speed win: a shard checking
~7 watches finishes a lap in seconds instead of the ~2-2.5 minutes a
single job checking all 40+ took before.

Each shard also writes to its own state file
(`state/shard-1.json` etc.), so the 6 parallel jobs never race or
conflict trying to commit to the same file.

## How the continuous cycling works

Instead of waiting on GitHub's 5-minute minimum schedule interval, each
shard's job loops internally: it checks its ~7 watches, waits about 15
seconds, then checks again — over and over, non-stop, independently of
the other 5 shards. Since each shard only has a handful of watches, a
lap normally finishes in well under a minute, so the real-world cadence
per shard lands around **every 15-45 seconds** rather than a precise
metronome.

GitHub caps any single job at 6 hours no matter what, so each shard's
loop stops itself after ~5h40m and lets that run end cleanly. The
`*/30 * * * *` schedule in the workflow is just a safety net per shard —
it starts a fresh run for a shard within 30 minutes if that shard's
long-running job ever ends early (crash, runner hiccup, the 5h40m
cutoff, etc). While a shard is already looping, extra schedule triggers
for it just queue harmlessly rather than starting a duplicate, thanks
to that shard's own `concurrency` group in the workflow file.

One tradeoff worth knowing: checking this often hits each retailer's
site noticeably more often than every 5 minutes did. That's still well
within normal human-browsing territory, not scraping-bot volume, but it
does raise the odds versus before of a heavily bot-protected site
(Amazon, Target) temporarily blocking or CAPTCHA-gating the runner's
traffic — see "Sites blocking the runner's IP" below. If that starts
happening a lot, slowing back down is a one-line change (see below).

**To slow the cadence down**: edit the `sleep 15` line in the "Run
checks continuously for this shard" step — a bigger number means more
time between cycles for every shard (e.g. `sleep 60` for a noticeably
slower pace).

**To go back to one unsharded job on a plain 5-minute schedule**: ask
and I can revert the workflow/config/script changes for you — it's a
bigger edit than a one-liner since it touches the matrix, the config
split, and the `--config`/`--state` arguments in `check_stock.py`.

## 7. Adding more products or retailers

See `config/README.md` for the full explanation of the 6 shard files.
Short version: open whichever `config/shard-N.json` has the fewest
entries right now, copy an existing entry's shape, fill in the real
product URL, and set `retailer` to whichever key in `RETAILER_RULES`
(top of `check_stock.py`) matches that site's platform:

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
workflow changes needed for a new watch in an existing shard.

## Notes and limitations

- **Run time and concurrency**: since listing_watches also check the
  stock of every matching product they find, a shard's cycle can do
  more than its raw watch count in page loads (a listing watch can
  pull in several extra product pages). Checks within a shard still run
  concurrently rather than one at a time - `CONCURRENCY_LIMIT` in
  `check_stock.py` (default 6) caps how many page loads are in flight
  at once per shard. The log prints a "Run finished in Xs" line at the
  end of every cycle - keep an eye on that in the Actions tab; it's the
  main lever on cadence, along with the sharding and sleep settings
  described above. If a particular shard's cycles are creeping up (e.g.
  after adding several watches to it), move some of its entries to a
  lighter shard, or raise `CONCURRENCY_LIMIT`.
- **Speed**: the workflow splits checking across 6 parallel shard jobs,
  each looping continuously rather than relying on GitHub's 5-minute
  schedule minimum — see "How checking is split across shards" and "How
  the continuous cycling works" above for the real cadence and how to
  tune it. If you want faster/near-instant checks beyond that, the next
  step up is moving the same logic to a Cloudflare Workers Cron Trigger
  (free tier allows 1-minute schedules) — ask if you want that built
  out.
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
  in `config/shard-1.json` is sold by a third-party marketplace seller,
  not Big W itself, and was priced with an inflated "SAVE $300" badge —
  common for reseller listings during a hyped drop. It's included
  because it's a real, currently-live listing, but treat its price with
  more skepticism than a "Sold & shipped by Big W" listing.
- **Sites blocking the runner's IP**: GitHub Actions runners use
  well-known shared IP ranges, and heavily bot-protected sites (Amazon,
  Target, anything behind Cloudflare/Akamai) sometimes start silently
  blocking or CAPTCHA-gating that traffic over time, unrelated to
  anything being wrong with the config — and checking every 15-45
  seconds per shard (see above) somewhat raises those odds compared to
  a slower schedule. If a retailer that used to work starts reporting
  UNKNOWN on every run, this is the likely cause. Each store's watches
  all live in one shard (see `config/README.md`), so this would only
  ever affect that one shard, not the other five.
- **Discord webhook getting blocked (HTTP 403, "error code: 1010")**:
  early real-world runs hit this - Discord sits behind Cloudflare,
  which was rejecting the webhook POST because it went out with
  Python's default `urllib` user-agent, a common bot fingerprint. Fixed
  by sending a normal browser-looking User-Agent on that request. A
  related logging bug was fixed at the same time: the script used to
  log "ALERT sent" right after *attempting* a Discord post, even if
  Discord had just rejected it - so a failed delivery looked identical
  to a successful one in the log. It now only logs "ALERT sent" when
  Discord actually accepts the message, and logs "ALERT DELIVERY
  FAILED" (check the Discord webhook error line just above it) when it
  doesn't - so if you ever see that line, treat it as a real signal
  that a notification didn't reach your channel, not just noise.
- **Discord rate limits**: Discord caps a webhook at roughly 30
  messages/minute. With 6 shards now able to alert independently and
  simultaneously, a burst where several different retailers restock at
  once (e.g. right at a midnight launch) is a bit more likely to brush
  up against that limit than with one shard - the script doesn't
  currently retry on a 429.
- **Long-term dormancy**: GitHub auto-disables a scheduled workflow
  after 60 days with no repository activity, and each shard only
  commits when its own state file actually changes. Not a near-term
  concern given how fast this set is already moving (and six
  independently-committing shards make it even less likely all
  activity stops at once), but if you keep this running for months
  after things quiet down, check the Actions tab occasionally to make
  sure it's still firing.
- **This is a notify-only tool, by design**: it never adds to cart or
  checks out automatically, and that's intentional, not a missing
  feature - an auto-purchasing version would cross into scalping-bot
  territory that competes unfairly with other shoppers.
- State (what's already been seen/alerted) lives in `state/shard-1.json`
  through `state/shard-6.json`, one per shard, which each shard's job
  commits back to the repo whenever it changes — that's how it avoids
  re-alerting you for the same thing on every cycle.
