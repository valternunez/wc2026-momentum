# Automation — daily scrape (local) + publish (cloud)

The pipeline is split so scraping (residential) and publishing (cloud) stay separate:

| Stage | Where | What | Why there |
|-------|-------|------|-----------|
| Scrape + build parquet + snapshot | **Local** (your PC) | `scripts/daily.ps1` | Residential IP; FotMob source |
| Build + deploy site | **Cloud** (GitHub Actions) | `.github/workflows/publish.yml` | No scraping → can't be IP-blocked; runs on every push |

Git history is the snapshot system; `snapshots/<date>/summary.json` is the clean estimate-over-time
series the report charts.

> **Source = FotMob (default).** SofaScore hard IP-blocked us (banned even in a normal browser), so the
> momentum source is **FotMob**: a per-minute home-positive momentum series via its `/api/data/*`
> endpoints, authenticated with a computed `x-mas` header (`src/scrape/fotmob.py`). Runtime is light —
> plain `curl_cffi` + the header, **no browser, no cookie**. The SofaScore cookie/browser path is parked
> in the repo as a fallback if its ban lifts (`--source sofascore`).
>
> Commentary comes from **ESPN's open API** (`src/scrape/espn.py`), matched to each FotMob match by
> date + team names — this gives **exact hydration-break timing + VAR + injury** stoppages for the
> mechanism comparison. It's fetched automatically during the scrape; no extra setup. If ESPN can't be
> matched, hydration falls back to the nominal ~22'/67' marks. (ESPN is reachable from any normal IP.)

## 0. Prove the scrape works (do this FIRST, from your home machine)

```powershell
python -m uv sync                                              # base deps
python -m uv run python -m src.scrape.fotmob --check-secret    # confirms the x-mas header builds
python -m uv run python -m src.scrape.fotmob --date=20260622   # discover WC match ids for a date
python -m uv run python -m src.scrape.fotmob 4506886           # health-check one match (id from above)
```
Expected from the last command: `[diag] OK …` with a non-zero `momentum points` count and detected
hydration stoppages. (FotMob doesn't block our IPs, so this should "just work" from any normal
connection.)

**Troubleshooting:**
- `FotMob GET failed … 403/Forbidden` while everything else works → FotMob rotated the signing secret.
  Replace `src/scrape/fotmob_secret_lyrics.txt` with the current lyrics (the easter-egg secret) from a
  maintained implementation, byte-exact.
- Empty `momentum points` → the match hasn't started / has no momentum yet; pick a finished match.

Once `[diag] OK` prints, the daily runner below will work.

## 1. One-time setup

```powershell
# from the repo root
python -m uv sync            # base deps (cookie scrape + report). Add --extra dev for tests.
# optional fallback only: python -m uv sync --extra browser && python -m uv run python -m playwright install chromium
gh repo create wc2026-momentum --public --source=. --remote=origin --push   # or create on github.com
```

Then on GitHub: **Settings → Pages → Build and deployment → Source = GitHub Actions.**
The first push (or a manual **Actions → Publish report site → Run workflow**) publishes the page.

## 2. Tell the scraper which matches to track

Put **FotMob** match ids in [`data/match_ids.json`](../data/match_ids.json):

```json
[4506886, 4506887, 4506888]
```

Discover ids for a date with `python -m uv run python -m src.scrape.fotmob --date=YYYYMMDD`. Already-
scraped matches are skipped, so it's safe to keep appending ids as the tournament progresses.

## 3. Schedule the daily run (Windows Task Scheduler)

Runs every morning at 08:30 through the final. `pwsh` if you have PowerShell 7, else `powershell`.
FotMob scraping needs no browser/cookie/login, so a plain scheduled task is fine (no `/IT` required).

```powershell
$repo = "C:\Users\PC\Documents\Dev\hydration-break-analysis-at-26wc"
schtasks /Create /TN "WC2026 daily scrape" /SC DAILY /ST 08:30 /F `
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\daily.ps1`""
```

Verify / run-now / remove:
```powershell
schtasks /Query  /TN "WC2026 daily scrape"
schtasks /Run    /TN "WC2026 daily scrape"
schtasks /Delete /TN "WC2026 daily scrape" /F   # after the final (July 19, 2026)
```

PC off for a day? No problem — finished matches are immutable, so the next run backfills.

## 4. Manual run / rebuild

```powershell
uv run python -m src.pipeline --ids-file data/match_ids.json --date 2026-06-22  # scrape + snapshot
uv run python -m src.pipeline --no-scrape                                       # rebuild parquet only
uv run python -m src.report.build_site                                          # build site/ locally
```

## Troubleshooting scraping
Default path: reuse your Chrome `cf_clearance` cookie (`src/scrape/cookies.py`) + curl_cffi. Plain
curl_cffi gets a CF "challenge"; an automated browser gets a flat 403 "Forbidden" (bot detection) —
so we replay your human browser's clearance instead.
- `No 'cf_clearance' cookie found` → open a SofaScore **match page** in Chrome first (the homepage
  isn't enough; the API cookie is set only when the app calls `api.sofascore.com`).
- `403` with a cookie present → expired or UA mismatch; reload a match page in the **same** Chrome.
- Reads **Chrome** by default; for another browser, adjust `make_cookie_client(browser=...)`.
- Fallbacks: `--browser` (Playwright; usually CF-blocked here), or the experimental **ScraperFC**
  library (https://scraperfc.readthedocs.io) which wraps a Sofascore scraper.
