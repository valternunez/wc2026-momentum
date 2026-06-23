# Railway daily scrape (cloud twin of `scripts/daily.ps1`)

Always-on daily refresh so it doesn't depend on the home PC being awake. **Verified:** FotMob's API
answers 200 from Railway's datacenter IP (unlike SofaScore), so the scrape can run here. Each run pulls
the repo onto a volume, scrapes finished WC2026 matches, rebuilds the parquet + site, and pushes to
GitHub — the existing `publish.yml` CI then redeploys the Pages site.

## Pieces
- `Dockerfile` — python:3.12-slim + git + uv + `daily.sh` (the repo is cloned at runtime, not baked in).
- `daily.sh` — clone/fast-forward the repo on the volume → `pipeline --discover-days 3 … --date <UTC>` →
  `build_site` → commit & push.

## Railway setup (project `wc2026-momentum`)
1. **Service** built from this directory's `Dockerfile`.
2. **Volume** mounted at **`/data`** (persists the working clone, `.venv`, and `data/raw` so scraping
   stays incremental).
3. **Variables**:
   - `GH_TOKEN` — GitHub **fine-grained PAT** scoped to `valternunez/wc2026-momentum`, **Contents:
     Read+Write** (set this yourself in Railway → Variables; never commit it).
   - `FOTMOB_SECRET_B64` — base64 of the byte-exact FotMob lyrics file (read by `fotmob._secret`).
   - `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` — optional commit identity.
4. **Cron schedule**: `30 13 * * *` (13:30 UTC). The container runs once and exits; Railway re-runs it
   on the next trigger.

The local Windows Task Scheduler job is kept as a fallback; both pushing is git-safe (identical data ⇒
one push wins, the other is a no-op).
