"""Tests for momentum windowing + team-perspective expansion (CLAUDE.md: required)."""

from __future__ import annotations

from src.features.momentum_features import COLUMNS, expand_stoppage_rows, window_stats
from src.parse.stoppages import detect_stoppages
from src.pipeline import assemble_rows


def _series(values_by_minute: dict[int, float]) -> list[dict[str, float]]:
    return [{"minute": float(m), "value": float(v)} for m, v in values_by_minute.items()]


def test_window_mean_and_delta_basic():
    # pre minutes 17-21 = +10 ; post minutes 23-27 = -10 ; break at 22
    series = _series({m: 10 for m in range(17, 22)} | {m: -10 for m in range(23, 28)})
    w = window_stats(series, center=22.0, window=5)
    assert w["pre_mean"] == 10.0
    assert w["post_mean"] == -10.0
    assert w["delta"] == -20.0


def test_window_excludes_break_minute_and_flags_short_windows():
    series = _series({22: 999})  # only the break minute itself
    w = window_stats(series, center=22.0, window=5)
    assert w["pre_mean"] is None and w["post_mean"] is None and w["delta"] is None


def test_window_slope_sign():
    # rising momentum before the break
    series = _series({17: 0, 18: 2, 19: 4, 20: 6, 21: 8})
    w = window_stats(series, center=22.0, window=5)
    assert w["pre_slope"] is not None and w["pre_slope"] > 0


def test_expand_two_rows_with_mirrored_perspectives():
    meta = {"match_id": 1, "home_team": "H", "away_team": "A", "start_timestamp": 1781000000}
    stoppage = {
        "stoppage_id": "1-00", "stoppage_type": "hydration", "clock_minute": 22.0,
        "real_duration_seconds": None,
        "home_score_pre": 1, "away_score_pre": 0,
        "red_cards_home_pre": 0, "red_cards_away_pre": 0,
        "sub_made_during_break": False, "subs_count_home": 0, "subs_count_away": 0,
    }
    series = _series({m: 10 for m in range(17, 22)} | {m: -10 for m in range(23, 28)})
    rows = expand_stoppage_rows(meta, stoppage, series)
    assert len(rows) == 2
    home = next(r for r in rows if r["is_home"])
    away = next(r for r in rows if not r["is_home"])
    # home was on top pre-break and loses momentum; away gains the mirror image
    assert home["momentum_delta"] == -away["momentum_delta"]
    assert home["momentum_delta"] < 0 < away["momentum_delta"]
    assert home["score_diff_pre"] == 1 and away["score_diff_pre"] == -1


def test_assemble_rows_full_schema_and_pairing(match_inputs):
    rows = assemble_rows(
        match_inputs["meta"], match_inputs["momentum"],
        match_inputs["incidents"], match_inputs["commentary"],
    )
    # 5 stoppages * 2 perspectives
    assert len(rows) == 10
    # every row has exactly the schema columns
    for r in rows:
        assert set(r.keys()) == set(COLUMNS)
    # the team that was on top before each hydration break loses momentum
    hyd_home = [r for r in rows if r["stoppage_type"] == "hydration" and r["is_home"]]
    assert all(r["momentum_delta"] < 0 for r in hyd_home)
