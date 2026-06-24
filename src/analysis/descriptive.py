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


def _isbreak_coef(rows: np.ndarray) -> float:
    """OLS coefficient on is_break in delta ~ 1 + is_break + pre. NaN if unfittable."""
    if rows.shape[0] < 3 or np.unique(rows[:, 1]).size < 2:
        return float("nan")
    y = rows[:, 0]
    x = np.column_stack([np.ones(rows.shape[0]), rows[:, 1], rows[:, 2]])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    return float(beta[1])


def gap_adjusted_ci(
    df: pl.DataFrame, placebo: pl.DataFrame, *, n_boot: int = 5000, seed: int = 7
) -> dict | None:
    """Level-adjusted break-vs-no-break gap for the on-top team, with a match-clustered bootstrap CI.

    Pools on-top hydration-break rows (is_break=1) with on-top within-2026 placebo rows (is_break=0)
    and estimates the coefficient on is_break in

        momentum_delta ~ is_break + momentum_pre_5min_mean

    i.e. the EXTRA momentum the leader sheds after a mandated break, beyond what its pre-break level
    already predicts — netting out the regression-to-the-mean gradient that a raw mean-difference
    leaves in (the placebo and the breaks sit at different pre-momentum levels). Resamples MATCHES
    (the cluster) for the interval. Returns {gap, lo, hi, n_break, n_placebo, n_matches} or None.
    `gap` is signed like momentum_delta: negative = the break bites harder than a quiet minute.
    """
    hyd = on_top_rows(df).filter(pl.col("stoppage_type") == "hydration")
    plc = on_top_rows(placebo)
    if hyd.is_empty() or plc.is_empty():
        return None

    def by_match(frame: pl.DataFrame, is_break: float) -> dict[str, list[tuple]]:
        out: dict[str, list[tuple]] = {}
        for r in frame.select(["match_id", "momentum_delta", "momentum_pre_5min_mean"]).iter_rows():
            out.setdefault(r[0], []).append((r[1], is_break, r[2]))
        return out

    hb, pb = by_match(hyd, 1.0), by_match(plc, 0.0)
    matches = sorted(set(hb) | set(pb))

    def stack(ms: list[str]) -> np.ndarray:
        acc: list[tuple] = []
        for m in ms:
            acc.extend(hb.get(m, ()))
            acc.extend(pb.get(m, ()))
        return np.array(acc, dtype=float) if acc else np.empty((0, 3))

    point = _isbreak_coef(stack(matches))
    if np.isnan(point):
        return None
    rng = np.random.default_rng(seed)
    draws = np.array([c for _ in range(n_boot)
                      if not np.isnan(c := _isbreak_coef(stack(list(rng.choice(matches, size=len(matches), replace=True)))))])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {
        "gap": float(point), "lo": float(lo), "hi": float(hi),
        "n_break": hyd.height, "n_placebo": plc.height,
        "n_matches": len(set(hb) | set(pb)),
    }


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
