# CLAUDE.md — agent guidance

This is a **research project, not production code.** Prioritize clarity and reproducibility over
abstraction. No premature OOP. Functions over classes until a class earns its keep.

## Hard rules
- **Persist raw scraped data to `data/raw/` before any parsing.** Never re-scrape during analysis —
  read from disk.
- **Every result that appears in the writeup must be produced by code in this repo,
  deterministically, from `data/processed/stoppages.parquet`.**
- When in doubt about statistical methodology (FE specification, clustering, bootstrap design),
  **stop and ask** rather than guessing — the causal claims are the whole point of the project.
- Prefer **polars** over pandas for new code. If extending pandas code, don't mix.
- Tests are required for **stoppage-detection** logic and **momentum-windowing** logic. Other code
  can ship without tests.
- Commit raw-data fixtures (one match) to `tests/fixtures/` so the pipeline can be tested offline.

## Data publishing policy
Derived-data-only. `data/raw/` and `data/interim/` are gitignored. We commit `data/processed/`
(the parquet) and `snapshots/` (dated summaries). Respect SofaScore/FotMob ToS — do not publish
raw scraped payloads.

## Architecture: split acquisition from publishing
- **Local** (Windows Task Scheduler, home IP) does ALL scraping → parses → writes processed parquet
  + a dated snapshot → commits & pushes. See `scripts/daily.ps1`.
- **Cloud** (GitHub Actions) NEVER scrapes. On push it rebuilds the report site from the committed
  parquet and deploys to GitHub Pages. See `.github/workflows/publish.yml`.
- Git history is the snapshot system; `snapshots/<date>/summary.json` is a clean estimate-over-time
  series.

## Run
```
uv sync                                   # base deps (lean: scrape + report)
uv sync --extra events --extra dev        # + socceraction/pandas + pytest
uv run python -m src.pipeline --help
uv run pytest
uv run python -m src.report.build_site
```

## Layout
- `src/scrape/`  — sofascore.py, fotmob.py, commentary.py (network only; persist raw)
- `src/parse/`   — stoppages.py (stoppage detection → stoppage-level rows)
- `src/features/`— momentum_features.py (5-min pre/post windowing)
- `src/analysis/`— descriptives, FE regression, placebos
- `src/viz/`     — chart functions (plotly web + mplsoccer static)
- `src/report/`  — build_site.py (parquet + writeup → site/index.html)
