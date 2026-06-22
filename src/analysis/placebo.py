"""Placebo break-time analysis (Phase-3 robustness).

PROJECT_BRIEF.md: run the SAME windowing at fake break times (e.g. 17′ and 62′,
5 min before the real marks) in matches without actual stoppages there. If we see
an "effect" at placebo times, the design is broken (regression to the mean).

This reuses `expand_stoppage_rows` so placebo windows are computed identically to
real ones; the rows are tagged stoppage_type="placebo" and can be fed to the same
`effect_by_type` aggregation for an apples-to-apples comparison.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from src.features.momentum_features import COLUMNS, expand_stoppage_rows
from src.scrape import sofascore

# Default placebo minutes: 5' before each nominal hydration mark (brief §Phase 3).
PLACEBO_MINUTES = (17.0, 62.0)


def _placebo_stoppage(match_id: Any, idx: int, minute: float) -> dict[str, Any]:
    """A minimal stoppage record at a placebo minute (no real incident context)."""
    return {
        "match_id": match_id,
        "stoppage_id": f"{match_id}-placebo{idx}",
        "stoppage_type": "placebo",
        "clock_minute": minute,
        "real_duration_seconds": None,
        "home_score_pre": 0, "away_score_pre": 0,
        "red_cards_home_pre": 0, "red_cards_away_pre": 0,
        "sub_made_during_break": False, "subs_count_home": 0, "subs_count_away": 0,
    }


def placebo_rows_for_match(match_id: int | str, minutes=PLACEBO_MINUTES) -> list[dict[str, Any]]:
    raw = sofascore.load_raw(match_id)
    if not raw.get("graph") or not raw.get("event"):
        return []
    meta = sofascore.parse_match_meta(raw["event"])
    momentum = sofascore.parse_momentum(raw["graph"])
    rows: list[dict[str, Any]] = []
    for i, minute in enumerate(minutes):
        rows.extend(expand_stoppage_rows(meta, _placebo_stoppage(meta["match_id"], i, minute), momentum))
    return rows


def build_placebo_table(match_ids: list[str], minutes=PLACEBO_MINUTES) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for mid in match_ids:
        rows.extend(placebo_rows_for_match(mid, minutes))
    if not rows:
        return pl.DataFrame(schema={c: pl.Utf8 for c in COLUMNS})
    return pl.DataFrame(rows).select(COLUMNS)
