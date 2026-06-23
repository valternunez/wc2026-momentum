"""Placebo break-time helpers (Phase-3 robustness).

Run the SAME windowing at fake break times (no real stoppage there); an "effect" at placebo
times would mean the design is broken (regression to the mean). The same-units placebos that
actually run are FotMob-based — see `fotmob_placebo.py` (CWC 2025, WC 2022) and
`historical_placebo.py` (2022 via StatsBomb xT). This module now only provides the shared
placebo-stoppage record + the default placebo minutes those builders import.
"""

from __future__ import annotations

from typing import Any

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
