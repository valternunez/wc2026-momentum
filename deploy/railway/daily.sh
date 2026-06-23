#!/usr/bin/env bash
# Railway daily runner — the cloud twin of scripts/daily.ps1.
#
# Each cron run: pull the latest repo onto the persistent volume, scrape finished WC2026
# matches (FotMob answers from Railway's IP — verified), rebuild the parquet + site, and
# push to GitHub. The existing publish.yml CI then redeploys the Pages site.
#
# Env required: GH_TOKEN (fine-grained PAT, contents:write), FOTMOB_SECRET_B64.
# Optional: GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, REPO_SLUG (default valternunez/wc2026-momentum).
set -euo pipefail

SLUG="${REPO_SLUG:-valternunez/wc2026-momentum}"
WORK="${WORK_DIR:-/data/repo}"
AUTH="https://x-access-token:${GH_TOKEN}@github.com/${SLUG}.git"

export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-wc2026-bot}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-wc2026-bot@users.noreply.github.com}"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

# Clone once onto the volume, then fast-forward to the latest committed code + data each run.
if [ ! -d "$WORK/.git" ]; then
  echo "[railway-daily] cloning $SLUG -> $WORK"
  git clone --depth 1 "$AUTH" "$WORK"
fi
cd "$WORK"
git remote set-url origin "$AUTH"
git fetch --depth 1 origin main
git reset --hard origin/main   # data/raw is gitignored, so it persists on the volume

# Base deps (.venv lives on the volume, so this is fast after the first run).
uv sync

TODAY="$(date -u +%F)"
echo "[railway-daily] $TODAY — discover + scrape + build"
uv run python -m src.pipeline --discover-days 3 --ids-file data/match_ids.json --date "$TODAY"
uv run python -m src.report.build_site

git add data/processed snapshots reports/figures data/match_ids.json
if git diff --cached --quiet; then
  echo "[railway-daily] no changes to commit"
else
  git commit -m "data: daily update $TODAY (railway)"
  git push origin main
  echo "[railway-daily] pushed $TODAY"
fi
