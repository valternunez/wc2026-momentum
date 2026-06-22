# Data directory

## Policy: derived data only
This repo commits **only derived data**. Raw provider payloads are never committed.

| Path | Tracked in git? | Contents |
|------|-----------------|----------|
| `data/raw/` | **No** (gitignored) | Untouched scraped JSON/HTML. Local reproducibility source on the scraping machine. |
| `data/interim/` | **No** (gitignored) | Parsed-but-not-joined intermediates. |
| `data/processed/` | **Yes** | `stoppages.parquet` — the analysis-ready stoppage-level table. |

`snapshots/` (repo root) holds dated `summary.json` files: one per daily run, capturing the key
aggregates (mean momentum delta by stoppage type, N, CIs) so we can chart how the estimate evolves
as the tournament progresses.

## Provenance & ToS
Momentum series and match events come from third-party providers (SofaScore primary, FotMob
cross-check) and commentary feeds. These remain subject to the providers' Terms of Service. We do
not redistribute raw payloads. Historical baselines use StatsBomb Open Data (separately licensed).

## Stoppage-level schema (`data/processed/stoppages.parquet`)
Unit of analysis: one stoppage, **two rows per stoppage** (one per team perspective). See
`src/parse/stoppages.py` for the authoritative column list and `PROJECT_BRIEF.md` for definitions.
