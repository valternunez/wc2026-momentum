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
# With a token we can push; without one we still clone the PUBLIC repo read-only (validation run).
if [ -n "${GH_TOKEN:-}" ]; then
  REMOTE="https://x-access-token:${GH_TOKEN}@github.com/${SLUG}.git"
else
  REMOTE="https://github.com/${SLUG}.git"
  echo "[railway-daily] no GH_TOKEN set — public read only; push will be skipped"
fi

export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-wc2026-bot}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-wc2026-bot@users.noreply.github.com}"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

# Clone once onto the volume, then fast-forward to the latest committed code + data each run.
if [ ! -d "$WORK/.git" ]; then
  echo "[railway-daily] cloning $SLUG -> $WORK"
  git clone --depth 1 "$REMOTE" "$WORK"
fi
cd "$WORK"
git remote set-url origin "$REMOTE"
git fetch --depth 1 origin main
git reset --hard origin/main   # data/raw is gitignored, so it persists on the volume

# Base deps (.venv lives on the volume, so this is fast after the first run).
uv sync

TODAY="$(date -u +%F)"
echo "[railway-daily] $TODAY — discover + scrape + build"
uv run python -m src.pipeline --discover-days 3 --ids-file data/match_ids.json --date "$TODAY"
uv run python -m src.report.build_site
# Refresh committed social artifacts (og cards, story stills, story MP4) when the numbers move.
# Best-effort: skips cleanly unless this runner installed the render extras (uv sync --extra browser
# --extra media + playwright install chromium). The local daily runner is the primary renderer.
uv run python -m src.pipeline --refresh-social || true

git add data/processed snapshots reports/figures data/match_ids.json
if git diff --cached --quiet; then
  echo "[railway-daily] no changes to commit"
elif [ -z "${GH_TOKEN:-}" ]; then
  echo "[railway-daily] changes built OK but GH_TOKEN unset — skipping push (validation run)"
else
  git commit -m "data: daily update $TODAY (railway)"
  # main may have advanced since our fetch (the residential Task Scheduler runner, or a manual
  # push). Rebase our single data commit and retry so a concurrent update is integrated rather
  # than lost to a non-fast-forward rejection (which previously failed the whole job).
  pushed=0
  for attempt in 1 2 3; do
    if git push origin main; then pushed=1; break; fi
    echo "[railway-daily] push rejected (attempt $attempt) — rebasing onto origin/main"
    git fetch origin main && git rebase origin/main || git rebase --abort || true
  done
  if [ "$pushed" = 1 ]; then
    echo "[railway-daily] pushed $TODAY"
  else
    echo "[railway-daily] push failed after retries" >&2
    exit 1
  fi
fi
