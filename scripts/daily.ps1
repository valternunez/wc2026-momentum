<#
  daily.ps1 — local daily runner (Windows Task Scheduler).

  Scrapes any new/finished WC2026 matches from a residential IP, rebuilds the
  processed parquet, writes a dated snapshot, and pushes. CI then rebuilds the
  Pages site from what we pushed (CI never scrapes). See reports/automation.md.

  Idempotent: matches already scraped are skipped; missed days self-heal because
  a finished match's momentum series never changes.
#>
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Resolve uv (PATH install) or fall back to the pip-installed module.
function Invoke-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { & uv @args }
    else { & python -m uv @args }
}

$today = Get-Date -Format "yyyy-MM-dd"
Write-Host "[daily] $today — scraping + building"

# Edit data/match_ids.json to list the SofaScore event ids to track.
Invoke-Uv run python -m src.pipeline --ids-file data/match_ids.json --date $today

# Optional: build the site locally too (CI also builds it on push).
Invoke-Uv run python -m src.report.build_site

# Commit only derived data (raw is gitignored). Skip cleanly if nothing changed.
git add data/processed snapshots reports
$changed = git status --porcelain data/processed snapshots reports
if ($changed) {
    git commit -m "data: daily snapshot $today"
    git push
    Write-Host "[daily] pushed snapshot $today"
} else {
    Write-Host "[daily] no changes to commit"
}
