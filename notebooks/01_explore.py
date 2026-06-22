"""Exploration notebook (marimo).

Run:  uv run --extra notebook marimo edit notebooks/01_explore.py

Reads the processed parquet (never re-scrapes) and shows the conditioned effect by
stoppage type. A scratchpad for Phase-1 descriptives — the report site is the
deliverable, this is for poking at the data.
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl

    from src.analysis.descriptive import effect_by_type, load_processed
    from src.paths import STOPPAGES_PARQUET

    return STOPPAGES_PARQUET, effect_by_type, load_processed, pl


@app.cell
def _(STOPPAGES_PARQUET, load_processed):
    df = load_processed() if STOPPAGES_PARQUET.exists() else None
    df
    return (df,)


@app.cell
def _(df, effect_by_type):
    effects = effect_by_type(df) if df is not None and not df.is_empty() else []
    effects
    return (effects,)


@app.cell
def _(df):
    # momentum delta by type, team-on-top only
    if df is not None and not df.is_empty():
        from src.analysis.descriptive import on_top_rows

        on_top_rows(df).group_by("stoppage_type").agg(
            __import__("polars").col("momentum_delta").mean()
        )
    return


if __name__ == "__main__":
    app.run()
