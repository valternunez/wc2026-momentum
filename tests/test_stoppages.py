"""Tests for stoppage detection + commentary classification (CLAUDE.md: required)."""

from __future__ import annotations

from src.parse.stoppages import detect_stoppages
from src.scrape.commentary import classify_comment, normalize_lines


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
