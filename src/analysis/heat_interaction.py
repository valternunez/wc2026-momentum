"""Layer 1 of the acclimatization study: does the break bite HARDER in the heat?

Cheapest, most decision-relevant cut — and it needs no new scraping. The real WC2026
hydration-break rows already carry per-match `wbgt` and `dome` (filled by
`enrich.enrich_stoppages`). If a hydration break does something physiological, the
on-top momentum drop should DEEPEN as WBGT rises and SHRINK in climate-controlled
(domed) matches. If it doesn't, the −25 is just regression to the mean regardless of heat.

This is effect-MODIFICATION within WC2026, so it's identified off the same teams in the
same tournament — no cross-tournament confound. (Caveat: WC2026 is days old; cells are
small and will grow.) Everything here reads the committed stoppages.parquet.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, load_processed, on_top_rows


def _slope_cluster_ci(
    df: pl.DataFrame, x_col: str, y_col: str = "momentum_delta", *, n_boot: int = 2000, seed: int = 7
) -> tuple[float, float, float]:
    """OLS slope of y on x, with a 95% CI from resampling MATCHES (same clustering as the means).

    Returns (slope, lo, hi); NaNs if <3 points or x has no variance.
    """
    d = df.drop_nulls([x_col, y_col])
    if d.height < 3 or float(d[x_col].std() or 0.0) == 0.0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    matches = d["match_id"].unique().to_list()
    by_match = {
        m: (d.filter(pl.col("match_id") == m)[x_col].to_numpy(),
            d.filter(pl.col("match_id") == m)[y_col].to_numpy())
        for m in matches
    }
    point = float(np.polyfit(d[x_col].to_numpy(), d[y_col].to_numpy(), 1)[0])
    slopes = []
    for _ in range(n_boot):
        pick = rng.choice(matches, size=len(matches), replace=True)
        xs = np.concatenate([by_match[m][0] for m in pick])
        ys = np.concatenate([by_match[m][1] for m in pick])
        if float(xs.std()) == 0.0:
            continue
        slopes.append(float(np.polyfit(xs, ys, 1)[0]))
    if not slopes:
        return (point, float("nan"), float("nan"))
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    return point, float(lo), float(hi)


def _cell(df: pl.DataFrame, **boot_kw) -> dict[str, Any]:
    mean, lo, hi = cluster_bootstrap_ci(df, **boot_kw)
    return {"n": df.height, "n_matches": df["match_id"].n_unique() if df.height else 0,
            "mean": mean, "ci_lo": lo, "ci_hi": hi}


def heat_interaction(df: pl.DataFrame | None = None, **boot_kw) -> dict[str, Any]:
    """Break-effect-by-heat summary on the real WC2026 hydration rows (on top, pre>0).

    Returns the overall drop, the domed-vs-open-air split, an open-air cool-vs-hot split
    (median WBGT), and the per-°C slope of the drop on WBGT (open-air only).
    """
    df = load_processed() if df is None else df
    top = on_top_rows(df).filter(pl.col("stoppage_type") == "hydration")
    openair = top.filter(pl.col("dome") == False)  # noqa: E712 (polars needs ==, not `is`)
    wb = openair.drop_nulls("wbgt")
    out: dict[str, Any] = {
        "overall": _cell(top, **boot_kw),
        "domed": _cell(top.filter(pl.col("dome") == True), **boot_kw),  # noqa: E712
        "open_air": _cell(openair, **boot_kw),
        "wbgt_slope_per_C": None,
        "cool_half": None,
        "hot_half": None,
    }
    if wb.height >= 4:
        med = float(wb["wbgt"].median())
        out["wbgt_median"] = med
        out["cool_half"] = _cell(wb.filter(pl.col("wbgt") <= med), **boot_kw)
        out["hot_half"] = _cell(wb.filter(pl.col("wbgt") > med), **boot_kw)
        s, slo, shi = _slope_cluster_ci(wb, "wbgt", **boot_kw)
        out["wbgt_slope_per_C"] = {"slope": s, "ci_lo": slo, "ci_hi": shi}
    return out


def _fmt(c: dict[str, Any] | None) -> str:
    if not c or c.get("mean") is None or (isinstance(c.get("mean"), float) and c["mean"] != c["mean"]):
        return "   n/a"
    return f"{c['mean']:+6.1f} [{c['ci_lo']:+.1f}, {c['ci_hi']:+.1f}]  (n={c['n']}, {c['n_matches']}m)"


def print_heat_interaction(res: dict[str, Any]) -> None:
    print("\n=== Break x heat (WC2026 hydration breaks, team on top) ===")
    print(f"  overall      {_fmt(res['overall'])}")
    print(f"  domed        {_fmt(res['domed'])}")
    print(f"  open-air     {_fmt(res['open_air'])}")
    if res.get("cool_half"):
        print(f"  cool half    {_fmt(res['cool_half'])}   (WBGT <= {res['wbgt_median']:.1f})")
        print(f"  hot half     {_fmt(res['hot_half'])}   (WBGT >  {res['wbgt_median']:.1f})")
    sl = res.get("wbgt_slope_per_C")
    if sl and sl["slope"] == sl["slope"]:  # not NaN
        print(f"  slope/C      {sl['slope']:+.2f} [{sl['ci_lo']:+.2f}, {sl['ci_hi']:+.2f}]  "
              "(<0 => drop deepens with heat)")
    print("  note: WC2026 is early — these cells are small and grow as matches accrue.")


if __name__ == "__main__":
    print_heat_interaction(heat_interaction())
