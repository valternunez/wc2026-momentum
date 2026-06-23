<#
  daily.ps1 - local daily runner (Windows Task Scheduler).

  Auto-discovers finished WC2026 matches from the last few days (FotMob), scrapes any
  new ones + ESPN commentary, rebuilds the processed parquet, regenerates the per-match
  momentum grid, writes a dated snapshot, commits, and pushes. CI then rebuilds the Pages
  site from what we pushed (CI never scrapes). See reports/automation.md.

  Idempotent: matches already scraped are skipped; missed days self-heal because a
  finished match's momentum series never changes. Source defaults to FotMob.

  Writes a heartbeat to logs/last_run.json (gitignored) so a stalled/failed run is visible.
#>
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Resolve uv (PATH install) or fall back to the pip-installed module.
function Invoke-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { & uv @args }
    else { & python -m uv @args }
}

$today = Get-Date -Format "yyyy-MM-dd"
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
function Write-Heartbeat($status, $note) {
    $obj = [ordered]@{ time = (Get-Date).ToString("o"); date = $today; status = $status; note = $note }
    ($obj | ConvertTo-Json -Compress) | Out-File -FilePath "logs/last_run.json" -Encoding ascii
    "$((Get-Date).ToString('s'))  $status  $note" | Out-File -FilePath "logs/daily.log" -Append -Encoding ascii
}

Write-Host "[daily] $today - discover + scrape + build"

# Build steps: on any failure, record the heartbeat and re-raise (task shows as failed).
try {
    Invoke-Uv run python -m src.pipeline --discover-days 3 --ids-file data/match_ids.json --date $today
    Invoke-Uv run python -m src.report.build_site
} catch {
    Write-Heartbeat "FAIL" "$($_.Exception.Message)"
    Write-Host "[daily] FAILED: $($_.Exception.Message)"
    throw
}

# Commit only derived data (raw is gitignored). Skip cleanly if nothing changed.
git add data/processed snapshots reports/figures data/match_ids.json
$changed = git status --porcelain data/processed snapshots reports/figures data/match_ids.json
if ($changed) {
    git commit -m "data: daily update $today"
    # Best-effort push: only if an 'origin' remote exists (works before the repo is created).
    if (git remote 2>$null | Select-String -Quiet '^origin$') {
        git push
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[daily] push failed; retrying in 10s"
            Start-Sleep -Seconds 10
            git push
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[daily] pushed $today"
            Write-Heartbeat "OK" "pushed"
        } else {
            Write-Host "[daily] push failed twice - data committed locally"
            Write-Heartbeat "PUSH_FAIL" "git push failed twice"
        }
    } else {
        Write-Host "[daily] committed $today (no 'origin' remote yet - skipping push)"
        Write-Heartbeat "OK" "committed, no remote"
    }
} else {
    Write-Host "[daily] no changes to commit"
    Write-Heartbeat "OK" "no changes"
}
