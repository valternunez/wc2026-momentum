<#
  daily.ps1 — local daily runner (Windows Task Scheduler).

  Auto-discovers finished WC2026 matches from the last few days (FotMob), scrapes any
  new ones + ESPN commentary, rebuilds the processed parquet, regenerates the per-match
  momentum grid, writes a dated snapshot, commits, and pushes. CI then rebuilds the Pages
  site from what we pushed (CI never scrapes). See reports/automation.md.

  Idempotent: matches already scraped are skipped; missed days self-heal because a
  finished match's momentum series never changes. Source defaults to FotMob.
#>
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Resolve uv (PATH install) or fall back to the pip-installed module.
function Invoke-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { & uv @args }
    else { & python -m uv @args }
}

$today = Get-Date -Format "yyyy-MM-dd"
Write-Host "[daily] $today — discover + scrape + build"

# Auto-discover finished WC matches over the last 3 days (merges into match_ids.json),
# scrape them + ESPN commentary, enrich, snapshot, and render the per-match panels.
Invoke-Uv run python -m src.pipeline --discover-days 3 --ids-file data/match_ids.json --date $today

# Build the editorial site locally too (CI also builds it on push).
Invoke-Uv run python -m src.report.build_site

# Commit only derived data (raw is gitignored). Skip cleanly if nothing changed.
git add data/processed snapshots reports/figures data/match_ids.json
$changed = git status --porcelain data/processed snapshots reports/figures data/match_ids.json
if ($changed) {
    git commit -m "data: daily update $today"
    # Best-effort push: only if an 'origin' remote exists (works before the repo is created).
    if (git remote 2>$null | Select-String -Quiet '^origin$') {
        git push; Write-Host "[daily] pushed $today"
    } else {
        Write-Host "[daily] committed $today (no 'origin' remote yet — skipping push)"
    }
} else {
    Write-Host "[daily] no changes to commit"
}
