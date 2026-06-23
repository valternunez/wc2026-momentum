"""Placebo break-time helpers (Phase-3 robustness).

Run the SAME windowing at fake break times (no real stoppage there); an "effect" at placebo
times would mean the design is broken (regression to the mean). The same-units placebos that
actually run are FotMob-based — see `fotmob_placebo.py` (CWC 2025, WC 2022) and
`historical_placebo.py` (2022 via StatsBomb xT). This module now only provides the shared
placebo-stoppage record. Each builder defines its own placebo minutes: the CWC 2025 and
WC 2022 placebos use the 22'/67' marks (matching the real break clock), and the within-2026
placebo uses quiet non-break minutes (10'/35'/55'/80').
"""

from __future__ import annotations

from typing import Any


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
