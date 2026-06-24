"""Does a LONGER hydration break bite harder? (descriptive, not causal.)

Now that real_duration_seconds is filled from ESPN's Start/End-delay match-clock deltas, we can
ask whether the on-top momentum drop deepens with how long the break actually lasted — the
question the "by type, not duration" caveat used to block. Same on-top + cluster-bootstrap
machinery as the rest of the project; this is a descriptive association, read with the usual
small-sample care, not a causal claim.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, load_processed, on_top_rows
from src.analysis.heat_interaction import _slope_cluster_ci


def _measured_hydration(df: pl.DataFrame) -> pl.DataFrame:
    return on_top_rows(df).filter(
        (pl.col("stoppage_type") == "hydration") & pl.col("real_duration_seconds").is_not_null()
    )


def duration_summary(df: pl.DataFrame | None = None) -> dict[str, Any]:
    """Distribution of measured hydration-break durations (seconds), for the site stat + readout."""
    df = load_processed() if df is None else df
    m = _measured_hydration(df)
    n_all = on_top_rows(df).filter(pl.col("stoppage_type") == "hydration").height
    if m.is_empty():
        return {"n": 0, "n_all": n_all}
    d = m["real_duration_seconds"]
    return {
        "n": m.height, "n_all": n_all,
        "min": int(d.min()), "max": int(d.max()),
        "median": int(round(float(d.median()))), "mean": int(round(float(d.mean()))),
    }


def duration_effect(df: pl.DataFrame | None = None, **boot_kw) -> dict[str, Any]:
    """Slope of momentum_delta on break length + a short-vs-long (median) split, on top + bootstrapped."""
    df = load_processed() if df is None else df
    top = _measured_hydration(df)
    if top.height < 6:
        return {"n": top.height, "note": "too few measured breaks"}
    med = float(top["real_duration_seconds"].median())
    short = top.filter(pl.col("real_duration_seconds") <= med)
    long_ = top.filter(pl.col("real_duration_seconds") > med)
    s, slo, shi = _slope_cluster_ci(top, "real_duration_seconds", **boot_kw)
    sm, sl, sh = cluster_bootstrap_ci(short, **boot_kw)
    lm, ll, lh = cluster_bootstrap_ci(long_, **boot_kw)
    return {
        "n": top.height, "n_matches": top["match_id"].n_unique(), "median_sec": int(round(med)),
        "slope_per_min": {"slope": s * 60, "ci_lo": slo * 60, "ci_hi": shi * 60},  # per +60s
        "short": {"n": short.height, "mean": sm, "ci_lo": sl, "ci_hi": sh},
        "long": {"n": long_.height, "mean": lm, "ci_lo": ll, "ci_hi": lh},
    }


def _fmt(c: dict | None) -> str:
    if not c or c.get("mean") is None or c["mean"] != c["mean"]:
        return "n/a"
    return f"{c['mean']:+6.1f} [{c['ci_lo']:+.1f}, {c['ci_hi']:+.1f}]  (n={c['n']})"


def print_duration_effect(df: pl.DataFrame | None = None) -> None:
    d = duration_summary(df)
    print("\n=== Hydration-break durations (ESPN start/end-delay seconds) ===")
    if not d.get("n"):
        print("  no measured durations"); return
    print(f"  measured {d['n']}/{d['n_all']} breaks | "
          f"min {d['min']}s · median {d['median']}s · mean {d['mean']}s · max {d['max']}s")
    e = duration_effect(df)
    if "slope_per_min" not in e:
        print(f"  effect: {e}"); return
    sl = e["slope_per_min"]
    print(f"  slope per +1 min  {sl['slope']:+.1f} [{sl['ci_lo']:+.1f}, {sl['ci_hi']:+.1f}]  "
          "(<0 => longer breaks bite harder)")
    print(f"  short half (<= {e['median_sec']}s)  {_fmt(e['short'])}")
    print(f"  long  half (>  {e['median_sec']}s)  {_fmt(e['long'])}")


if __name__ == "__main__":
    print_duration_effect()
