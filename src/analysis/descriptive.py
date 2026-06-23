"""Phase-1 descriptive analysis: the conditioned effect by stoppage type + CIs.

The pooled mean momentum_delta is ~0 by construction (two mirrored team rows per
stoppage), so the analysis conditions on the team that was ON TOP pre-break
(momentum_pre_5min_mean > 0). Hypothesis 1 predicts hydration breaks push
momentum AWAY from that team (negative delta).

Bootstrap CIs are clustered at the match level (the brief: multiple stoppages per
match are not independent) by resampling matches, not rows.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from src.paths import STOPPAGES_PARQUET


def load_processed(path=STOPPAGES_PARQUET) -> pl.DataFrame:
    return pl.read_parquet(path)


def on_top_rows(df: pl.DataFrame) -> pl.DataFrame:
    """Rows for the team that was on top of momentum pre-break."""
    return df.drop_nulls(["momentum_delta", "momentum_pre_5min_mean"]).filter(
        pl.col("momentum_pre_5min_mean") > 0
    )


def cluster_bootstrap_ci(
    df: pl.DataFrame, value_col: str = "momentum_delta", *, n_boot: int = 2000, seed: int = 7
) -> tuple[float, float, float]:
    """Mean + 95% CI by resampling MATCHES (cluster bootstrap). Returns (mean, lo, hi)."""
    if df.is_empty():
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    matches = df["match_id"].unique().to_list()
    by_match = {m: df.filter(pl.col("match_id") == m)[value_col].to_numpy() for m in matches}
    point = float(df[value_col].mean())
    means = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(matches, size=len(matches), replace=True)
        vals = np.concatenate([by_match[m] for m in pick])
        means[b] = vals.mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return point, float(lo), float(hi)


def pre_level_r2(df: pl.DataFrame) -> float | None:
    """R² of the leader's post-break swing on its pre-break level (on-top hydration breaks).

    Quantifies the regression-to-the-mean gradient: how much of momentum_delta is explained by
    how high a team was already riding when the whistle blew. Returns None if <3 points or no
    variance. This is a genuine variance-explained share (not a chart magnitude).
    """
    top = on_top_rows(df).filter(pl.col("stoppage_type") == "hydration")
    if top.height < 3:
        return None
    x = top["momentum_pre_5min_mean"].to_numpy()
    y = top["momentum_delta"].to_numpy()
    if float(x.std()) == 0.0 or float(y.std()) == 0.0:
        return None
    r = float(np.corrcoef(x, y)[0, 1])
    return r * r


def effect_by_type(df: pl.DataFrame, **boot_kw) -> list[dict]:
    """Per stoppage type: n, on-top mean delta, and a cluster-bootstrap 95% CI."""
    top = on_top_rows(df)
    out = []
    for stype in sorted(top["stoppage_type"].unique().to_list()):
        sub = top.filter(pl.col("stoppage_type") == stype)
        mean, lo, hi = cluster_bootstrap_ci(sub, **boot_kw)
        out.append(
            {
                "stoppage_type": stype,
                "n": sub.height,
                "n_matches": sub["match_id"].n_unique(),
                "mean_delta": mean,
                "ci_lo": lo,
                "ci_hi": hi,
            }
        )
    return out
