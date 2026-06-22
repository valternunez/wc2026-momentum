"""Historical placebo (Phase-3 robustness) on 2022 men's WC StatsBomb matches.

There were NO mandated hydration breaks at the 2022 WC, so applying the SAME
22'/67' windowing to those matches must show ~zero "effect" — any non-zero
conditioned delta is bias (regression to the mean), not a break effect.

There is also NO SofaScore momentum for 2022, so we use the event-derived
**xT-flow momentum proxy** (`event_features.event_momentum_series`) as the outcome
series and feed it through the SAME `expand_stoppage_rows` used for the real
SofaScore pipeline, tagging rows `stoppage_type="placebo"`. This mirrors
`src/analysis/placebo.py` exactly, swapping the series source.

Summary stats reuse `src/analysis/descriptive.py` (`on_top_rows`,
`cluster_bootstrap_ci`) so the conditioned (team-on-top) mean delta + clustered
bootstrap CI are computed identically to the main descriptives.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, on_top_rows
from src.features.event_features import event_momentum_series
from src.features.momentum_features import COLUMNS, expand_stoppage_rows
from src.scrape.statsbomb import fetch_matches

# Nominal hydration marks; placebo because no breaks were mandated in 2022.
PLACEBO_MINUTES = (22.0, 67.0)


def _match_meta(match_id: int) -> dict[str, Any] | None:
    """Minimal `meta` dict for `expand_stoppage_rows` from the 2022 WC match list."""
    for m in fetch_matches():
        if m["match_id"] == match_id:
            stage = (m.get("competition_stage") or {}).get("name")
            stadium = (m.get("stadium") or {}).get("name")
            return {
                "match_id": match_id,
                "home_team": m["home_team"]["home_team_name"],
                "away_team": m["away_team"]["away_team_name"],
                "start_timestamp": None,  # match_date is a string; keep date None
                "match_date": m.get("match_date"),
                "stage": stage,
                "venue_stadium": stadium,
                "venue_city": None,
            }
    return None


def _placebo_stoppage(match_id: int, idx: int, minute: float) -> dict[str, Any]:
    """Minimal stoppage record at a placebo minute (mirrors src/analysis/placebo.py)."""
    return {
        "match_id": match_id,
        "stoppage_id": f"{match_id}-histplacebo{idx}",
        "stoppage_type": "placebo",
        "clock_minute": minute,
        "real_duration_seconds": None,
        "home_score_pre": 0, "away_score_pre": 0,
        "red_cards_home_pre": 0, "red_cards_away_pre": 0,
        "sub_made_during_break": False, "subs_count_home": 0, "subs_count_away": 0,
    }


def placebo_rows_for_match(match_id: int, minutes=PLACEBO_MINUTES) -> list[dict[str, Any]]:
    """Two team-perspective rows per placebo minute, using the xT-flow series."""
    meta = _match_meta(match_id)
    if meta is None:
        return []
    series = event_momentum_series(match_id)
    if not series:
        return []
    # match_date from the StatsBomb string overrides the ts-derived (None) value.
    match_date = meta.get("match_date")
    rows: list[dict[str, Any]] = []
    for i, minute in enumerate(minutes):
        stoppage = _placebo_stoppage(match_id, i, minute)
        for row in expand_stoppage_rows(meta, stoppage, series):
            if match_date is not None:
                row["match_date"] = match_date
            rows.append(row)
    return rows


def build_historical_placebo_table(
    match_ids: list[int], minutes=PLACEBO_MINUTES
) -> pl.DataFrame:
    """Stoppage-level placebo table over the given 2022 WC match ids."""
    rows: list[dict[str, Any]] = []
    for mid in match_ids:
        rows.extend(placebo_rows_for_match(mid, minutes))
    if not rows:
        return pl.DataFrame(schema={c: pl.Utf8 for c in COLUMNS})
    return pl.DataFrame(rows).select(COLUMNS)


def summarize_placebo(df: pl.DataFrame, *, n_boot: int = 2000, seed: int = 7) -> dict[str, Any]:
    """Conditioned (team-on-top) mean momentum delta + cluster-bootstrap 95% CI.

    The pooled delta is ~0 by construction (mirrored rows); conditioning on the
    team that was on top pre-break (momentum_pre_5min_mean > 0) is where any
    regression-to-the-mean bias shows up. Returns mean/ci_lo/ci_hi/n/n_matches.
    A CI that excludes 0 here is a warning sign that the windowing itself is biased.
    """
    top = on_top_rows(df)
    mean, lo, hi = cluster_bootstrap_ci(top, "momentum_delta", n_boot=n_boot, seed=seed)
    return {
        "mean_delta": mean,
        "ci_lo": lo,
        "ci_hi": hi,
        "n": top.height,
        "n_matches": top["match_id"].n_unique() if top.height else 0,
    }
