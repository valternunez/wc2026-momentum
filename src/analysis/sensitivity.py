"""Window-length sensitivity for the hydration-break momentum effect.

The headline effect windows momentum 5 minutes either side of a break. Here we recompute the
on-top (leader-perspective) effect at windows {4, 5, 6} minutes to show it isn't an artifact of
that one choice. Reuses the tested `window_stats` (variable window) and `cluster_bootstrap_ci`
(match-clustered) so the 5-min row reproduces the published −24. Local-only (reads data/raw).

    uv run python -m src.analysis.sensitivity
"""

from __future__ import annotations

from typing import Any

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, load_processed
from src.features.momentum_features import window_stats
from src.scrape import fotmob

WINDOWS = (4.0, 5.0, 6.0)


def _hydration_marks(df: pl.DataFrame) -> list[dict[str, Any]]:
    return (df.filter(pl.col("stoppage_type") == "hydration")
            .select("match_id", "clock_minute").unique().sort(["match_id", "clock_minute"]).to_dicts())


def window_effect(window: float, df: pl.DataFrame | None = None) -> dict[str, Any]:
    """On-top leader momentum change at `window` minutes, with a match-clustered 95% CI."""
    df = load_processed() if df is None else df
    rows = []
    for mk in _hydration_marks(df):
        series = fotmob.parse_momentum(fotmob.load_raw(mk["match_id"]))  # home-positive
        if not series:
            continue
        st = window_stats(series, float(mk["clock_minute"]), window=window)
        pre, post = st["pre_mean"], st["post_mean"]
        if pre is None or post is None or pre == 0:
            continue
        # leader perspective: home-on-top (pre>0) keeps sign; away-on-top flips it
        leader_delta = (post - pre) if pre > 0 else -(post - pre)
        rows.append({"match_id": str(mk["match_id"]), "momentum_delta": leader_delta})
    bdf = pl.DataFrame(rows) if rows else pl.DataFrame(schema={"match_id": pl.Utf8, "momentum_delta": pl.Float64})
    mean, lo, hi = cluster_bootstrap_ci(bdf)
    return {"window": window, "mean": mean, "lo": lo, "hi": hi,
            "n": bdf.height, "matches": bdf["match_id"].n_unique() if bdf.height else 0}


def sweep(df: pl.DataFrame | None = None) -> list[dict[str, Any]]:
    df = load_processed() if df is None else df
    return [window_effect(w, df) for w in WINDOWS]


if __name__ == "__main__":
    print("Window-length sensitivity — on-top hydration-break momentum change\n")
    print(f"{'window':>7} | {'mean':>7} | {'95% CI':>18} | {'n':>4} | {'matches':>7}")
    print("-" * 56)
    for r in sweep():
        ci = f"[{r['lo']:+.1f}, {r['hi']:+.1f}]"
        print(f"{r['window']:>6.0f}m | {r['mean']:>+7.1f} | {ci:>18} | {r['n']:>4} | {r['matches']:>7}")
