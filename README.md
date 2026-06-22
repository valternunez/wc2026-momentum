# World Cup 2026 — Stoppage Momentum Analysis

Do FIFA's new **mandatory hydration breaks** (~22′ and ~67′) actually shift in-match momentum — and
if so, in whose favor? This project treats the 2026 World Cup's mandated breaks as a natural
experiment, using **per-minute momentum series** as the outcome and comparing hydration breaks
against other stoppages (VAR, injuries) of similar duration to isolate the mechanism.

> **Status:** live data collection through the 2026 final (July 19). The report site below
> regenerates daily as matches accumulate.

📊 **Live report:** https://valternunez.github.io/wc2026-momentum/ — auto-updates as matches are scraped.
📝 Full design: [`PROJECT_BRIEF.md`](PROJECT_BRIEF.md)

## How it works

```
LOCAL (daily, home IP)                         CLOUD (GitHub Actions, on push)
scrape new matches → data/raw/ (local)         build report site from committed parquet
parse → features → data/processed/*.parquet    deploy to GitHub Pages
write snapshots/<date>/summary.json
git commit + push  ───────────────────────────▶ (no scraping in CI — can't be IP-blocked)
```

Git history is the snapshot system; `snapshots/` additionally tracks how the estimate evolves as N
grows. Only **derived data** is committed — raw provider payloads stay local (ToS-respecting).

## Quickstart

```bash
uv sync                              # base deps
uv run python -m src.pipeline --matches 3   # thin slice: 3 matches end-to-end
uv run pytest                        # stoppage-detection + windowing tests
uv run python -m src.report.build_site      # build site/index.html locally
```

See [`reports/automation.md`](reports/automation.md) for daily scheduling setup.

## Method (summary)
- **Outcome:** signed per-minute momentum (SofaScore primary, FotMob cross-check), reframed to
  team-perspective, aggregated to 5-minute pre/post windows around each stoppage.
- **Identification:** duration-matched comparison of hydration vs VAR vs injury stoppages; placebo
  break times; 2022 WC historical placebo; explicit regression-to-the-mean control.
- See `PROJECT_BRIEF.md` for hypotheses, the full regression spec, and pitfalls handled.

## License
Code: MIT. Data: derived only, subject to provider ToS — see [`data/README.md`](data/README.md).
