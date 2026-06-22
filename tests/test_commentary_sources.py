"""Tests for the BBC/ESPN commentary adapters + cross-source reconciliation.

Pure parsers + reconcile run fully offline against the committed sample fixtures.
Any live network fetch is guarded with pytest.skip (residential-IP only).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.parse.reconcile import MINUTE_TOLERANCE, reconcile
from src.scrape.commentary import normalize_lines
from src.scrape.commentary_sources import (
    fetch_bbc_commentary,
    fetch_espn_commentary,
    parse_bbc,
    parse_espn,
)

SAMPLES = Path(__file__).parent / "fixtures" / "commentary_samples"


def _bbc_html() -> str:
    return (SAMPLES / "bbc_sample.html").read_text(encoding="utf-8")


def _espn_json() -> dict:
    return json.loads((SAMPLES / "espn_sample.json").read_text(encoding="utf-8"))


# --- BBC pure parser --------------------------------------------------------


def test_parse_bbc_extracts_lines_and_minutes():
    lines = parse_bbc(_bbc_html())
    # 6 posts in the fixture, all with text
    assert len(lines) == 6
    minutes = [ln["minute"] for ln in lines]
    # minute tokens kept as strings for normalize_lines to coerce
    assert minutes[0] == "14"
    assert "cooling break" in lines[1]["text"].lower()


def test_parse_bbc_types_after_normalize():
    norm = normalize_lines(parse_bbc(_bbc_html()))
    types = [ln["type"] for ln in norm]
    assert "hydration" in types
    assert "var" in types
    assert "injury" in types
    # the two hydration breaks (22', 67') both classify as hydration
    assert sum(t == "hydration" for t in types) == 2
    # minutes coerced to float
    assert norm[0]["minute"] == 14.0


def test_parse_bbc_empty_is_safe():
    assert parse_bbc("") == []
    assert parse_bbc("<html><body><p>no posts</p></body></html>") == []


# --- ESPN pure parser -------------------------------------------------------


def test_parse_espn_extracts_lines_and_minutes():
    lines = parse_espn(_espn_json())
    assert len(lines) == 6
    assert lines[1]["minute"] == "22"
    assert "cooling break" in lines[1]["text"].lower()


def test_parse_espn_types_after_normalize():
    norm = normalize_lines(parse_espn(_espn_json()))
    types = [ln["type"] for ln in norm]
    assert "hydration" in types
    assert "var" in types
    assert "injury" in types
    assert sum(t == "hydration" for t in types) == 2


def test_parse_espn_handles_gamepackage_nesting():
    nested = {"gamepackageJSON": _espn_json()}
    assert len(parse_espn(nested)) == 6


def test_parse_espn_empty_is_safe():
    assert parse_espn({}) == []
    assert parse_espn({"commentary": []}) == []


# --- reconciliation ---------------------------------------------------------


def test_reconcile_dedupes_hydration_reported_by_both_sources():
    bbc = normalize_lines(parse_bbc(_bbc_html()))
    espn = normalize_lines(parse_espn(_espn_json()))
    merged = reconcile([bbc, espn])

    hyd = [ln for ln in merged if ln["type"] == "hydration"]
    # both sources report a ~22' break and a ~67' break -> exactly 2 after dedupe
    assert len(hyd) == 2
    hyd_minutes = sorted(ln["minute"] for ln in hyd)
    assert abs(hyd_minutes[0] - 22.0) <= MINUTE_TOLERANCE
    assert abs(hyd_minutes[1] - 67.0) <= MINUTE_TOLERANCE


def test_reconcile_keeps_distinct_events():
    bbc = normalize_lines(parse_bbc(_bbc_html()))
    espn = normalize_lines(parse_espn(_espn_json()))
    merged = reconcile([bbc, espn])

    # var and injury survive as their own events
    assert any(ln["type"] == "var" for ln in merged)
    assert any(ln["type"] == "injury" for ln in merged)
    # BBC injury at 55', ESPN injury at 62' are >TOLERANCE apart -> NOT merged
    injuries = [ln for ln in merged if ln["type"] == "injury"]
    assert len(injuries) == 2


def test_reconcile_is_chronological():
    bbc = normalize_lines(parse_bbc(_bbc_html()))
    espn = normalize_lines(parse_espn(_espn_json()))
    merged = reconcile([bbc, espn])
    minutes = [ln["minute"] for ln in merged if ln["minute"] is not None]
    assert minutes == sorted(minutes)


def test_reconcile_prefers_richer_text():
    a = [{"minute": 22.0, "text": "Cooling break.", "type": "hydration"}]
    b = [{"minute": 22.5, "text": "Cooling break as the heat soars past 35C.", "type": "hydration"}]
    merged = reconcile([a, b])
    assert len(merged) == 1
    assert merged[0]["text"] == "Cooling break as the heat soars past 35C."


def test_reconcile_does_not_dedupe_plain_play():
    a = [{"minute": 5.0, "text": "Shot wide.", "type": "none"}]
    b = [{"minute": 5.0, "text": "Cleared away.", "type": "none"}]
    merged = reconcile([a, b])
    assert len(merged) == 2


def test_reconcile_fills_missing_minute_from_other_source():
    a = [{"minute": None, "text": "Hydration break.", "type": "hydration"}]
    b = [{"minute": 22.0, "text": "Hydration break.", "type": "hydration"}]
    merged = reconcile([a, b])
    assert len(merged) == 1
    assert merged[0]["minute"] == 22.0


# --- live fetch guards (residential IP only) --------------------------------


def test_fetch_bbc_live_skipped():
    pytest.skip("live network fetch; run from a residential IP only")
    fetch_bbc_commentary("https://www.bbc.com/sport/football/live/example", "example")


def test_fetch_espn_live_skipped():
    pytest.skip("live network fetch; run from a residential IP only")
    fetch_espn_commentary(123456)
