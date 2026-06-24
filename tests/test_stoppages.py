"""Tests for stoppage detection + commentary classification (CLAUDE.md: required)."""

from __future__ import annotations

from src.parse.stoppages import detect_stoppages
from src.scrape.commentary import classify_comment, normalize_lines
from src.scrape.espn import parse_commentary


# --- commentary classification ---------------------------------------------

def test_classify_hydration_variants():
    for text in [
        "The referee signals a cooling break.",
        "Players take a drinks break.",
        "A hydration break as temperatures soar.",
        "Time for a water break.",
    ]:
        assert classify_comment(text) == "hydration", text


def test_classify_var_injury_sub_none():
    assert classify_comment("VAR is checking a possible penalty.") == "var"
    assert classify_comment("On-field review under way.") == "var"
    assert classify_comment("Player down injured, receiving treatment.") == "injury"
    assert classify_comment("Substitution: Sub A comes on for Starter A.") == "substitution"
    assert classify_comment("A lovely passing move ends with a shot wide.") == "none"


def test_hydration_beats_generic_break_ordering():
    # 'cooling break' must classify as hydration, not fall through to other.
    assert classify_comment("We pause for a cooling break now.") == "hydration"


def test_minute_coercion_handles_stoppage_time():
    out = normalize_lines([{"minute": "90+2'", "text": "x"}, {"minute": "67'", "text": "y"}])
    assert out[0]["minute"] == 92.0
    assert out[1]["minute"] == 67.0


# --- detection over the synthetic fixture ----------------------------------

def test_detect_expected_types_and_count(match_inputs):
    s = detect_stoppages(match_inputs["meta"], match_inputs["incidents"], match_inputs["commentary"])
    types = sorted(x["stoppage_type"] for x in s)
    assert types == ["hydration", "hydration", "injury_huddle", "injury_no_huddle", "var"]


def test_hydration_clustered_near_nominal_marks(match_inputs):
    s = detect_stoppages(match_inputs["meta"], match_inputs["incidents"], match_inputs["commentary"])
    hyd = sorted(x["clock_minute"] for x in s if x["stoppage_type"] == "hydration")
    # 21' + 22' cluster -> ~21.5 ; lone 66'
    assert abs(hyd[0] - 21.5) < 0.6
    assert abs(hyd[1] - 66.0) < 0.6


# --- break duration from ESPN start/end-delay second deltas ------------------

def _hyd(s):
    return [x for x in s if x["stoppage_type"] == "hydration"]


def test_espn_parse_extracts_seconds_and_delay():
    summary = {"commentary": [
        {"time": {"displayValue": "23'", "value": 1335.0},
         "text": "Delay in match for a drinks break.",
         "play": {"type": {"text": "Start Delay"}, "clock": {"value": 1335.0},
                  "wallclock": "2026-06-12T02:23:02Z"}},
        {"time": {"displayValue": "25'", "value": 1465.0},
         "text": "Delay over. They are ready to continue.",
         "play": {"type": {"text": "End Delay"}, "clock": {"value": 1465.0},
                  "wallclock": "2026-06-12T02:25:12Z"}},
    ]}
    lines = parse_commentary(summary)
    assert lines[0]["seconds"] == 1335.0 and lines[0]["delay"] == "start"
    assert lines[1]["seconds"] == 1465.0 and lines[1]["delay"] == "end"


def test_hydration_duration_from_delay_pair():
    commentary = normalize_lines([
        {"minute": "22'", "text": "A drinks break is taken.", "seconds": 1320.0, "delay": "start"},
        {"minute": "24'", "text": "Delay over. Ready to continue.", "seconds": 1445.0, "delay": "end"},
    ])
    s = detect_stoppages({"match_id": "m1"}, [], commentary)
    assert _hyd(s)[0]["real_duration_seconds"] == 125  # 1445 - 1320


def test_hydration_duration_none_without_resume():
    commentary = normalize_lines([
        {"minute": "22'", "text": "A drinks break.", "seconds": 1320.0, "delay": "start"},
    ])
    s = detect_stoppages({"match_id": "m1"}, [], commentary)
    assert _hyd(s)[0]["real_duration_seconds"] is None


def test_hydration_duration_pairs_nearest_end():
    # an unrelated end-delay long after must not be chosen over the real resume
    commentary = normalize_lines([
        {"minute": "67'", "text": "Cooling break.", "seconds": 4020.0, "delay": "start"},
        {"minute": "69'", "text": "Delay over.", "seconds": 4110.0, "delay": "end"},
        {"minute": "80'", "text": "Delay over.", "seconds": 4800.0, "delay": "end"},
    ])
    s = detect_stoppages({"match_id": "m1"}, [], commentary)
    assert _hyd(s)[0]["real_duration_seconds"] == 90  # 4110 - 4020, not 4800


def test_hydration_duration_absent_seconds_is_none():
    # old-schema commentary (no seconds) still detects the break, just without a duration
    commentary = normalize_lines([{"minute": "22'", "text": "Drinks break."}])
    s = detect_stoppages({"match_id": "m1"}, [], commentary)
    assert _hyd(s) and _hyd(s)[0]["real_duration_seconds"] is None


def test_var_duration_from_generic_delay():
    # a VAR stoppage takes the nearest GENERIC (non-hydration) delay pair's duration
    commentary = normalize_lines([
        {"minute": "50'", "text": "VAR is checking a possible penalty.", "seconds": 3000.0},
        {"minute": "50'", "text": "Delay in match.", "seconds": 3000.0, "delay": "start"},
        {"minute": "51'", "text": "Delay over.", "seconds": 3050.0, "delay": "end"},
    ])
    s = detect_stoppages({"match_id": "m1"}, [], commentary)
    var = [x for x in s if x["stoppage_type"] == "var"]
    assert var and var[0]["real_duration_seconds"] == 50


def test_injury_huddle_vs_no_huddle_from_sub(match_inputs):
    s = {x["stoppage_type"]: x for x in detect_stoppages(
        match_inputs["meta"], match_inputs["incidents"], match_inputs["commentary"])}
    # injury at 55' has a sub at 56' -> huddle; injury at 75' has none -> no_huddle
    assert s["injury_huddle"]["sub_made_during_break"] is True
    assert s["injury_no_huddle"]["sub_made_during_break"] is False


def test_score_state_before_stoppage(match_inputs):
    s = detect_stoppages(match_inputs["meta"], match_inputs["incidents"], match_inputs["commentary"])
    first_hyd = min((x for x in s if x["stoppage_type"] == "hydration"), key=lambda r: r["clock_minute"])
    later = next(x for x in s if x["stoppage_type"] == "injury_no_huddle")  # 75'
    assert (first_hyd["home_score_pre"], first_hyd["away_score_pre"]) == (0, 0)  # goal is at 30'
    assert (later["home_score_pre"], later["away_score_pre"]) == (1, 0)


def test_red_card_not_counted_before_it_happens(match_inputs):
    # red card is at 82'; no stoppage before it should see a red card
    s = detect_stoppages(match_inputs["meta"], match_inputs["incidents"], match_inputs["commentary"])
    assert all(x["red_cards_home_pre"] == 0 and x["red_cards_away_pre"] == 0 for x in s)


def test_stoppage_ids_unique_and_chronological(match_inputs):
    s = detect_stoppages(match_inputs["meta"], match_inputs["incidents"], match_inputs["commentary"])
    ids = [x["stoppage_id"] for x in s]
    minutes = [x["clock_minute"] for x in s]
    assert len(set(ids)) == len(ids)
    assert minutes == sorted(minutes)
