"""Tests for the ESPN commentary layer that augments FotMob (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from src.parse.stoppages import detect_stoppages
from src.scrape import espn
from src.scrape.commentary import normalize_lines

SUMMARY = json.loads((Path(__file__).parent / "fixtures" / "espn_match" / "summary.json").read_text())


def test_parse_and_classify_commentary():
    lines = normalize_lines(espn.parse_commentary(SUMMARY))
    by_type = {x["type"] for x in lines}
    assert {"hydration", "var", "injury"} <= by_type
    # minutes coerced from "22'" etc.
    hyd = [x for x in lines if x["type"] == "hydration"]
    assert sorted(round(x["minute"]) for x in hyd) == [22, 67]


def test_canon_handles_divergences():
    # word order, hyphen/"and", accents, and aliases all canonicalise together
    assert espn.canon("DR Congo") == espn.canon("Congo DR")
    assert espn.canon("Bosnia and Herzegovina") == espn.canon("Bosnia-Herzegovina")
    assert espn.canon("Curaçao") == espn.canon("Curacao")
    assert espn.canon("USA") == espn.canon("United States")
    assert espn.canon("Korea Republic") == espn.canon("South Korea")
    assert espn.canon("Côte d'Ivoire") == espn.canon("Ivory Coast")


def test_teams_match_order_and_aliases():
    # fixture order swapped AND a word-order team name
    assert espn._teams_match("Portugal", "DR Congo", "Congo DR", "Portugal")
    # alias divergence
    assert espn._teams_match("USA", "Paraguay", "United States", "Paraguay")
    # genuinely different fixture does not match
    assert not espn._teams_match("Brazil", "Spain", "Argentina", "France")


def test_commentary_drives_stoppage_detection():
    """ESPN commentary alone yields hydration + VAR + injury stoppages."""
    meta = {"match_id": 1, "home_team": "H", "away_team": "A", "start_timestamp": 1781000000}
    commentary = normalize_lines(espn.parse_commentary(SUMMARY))
    stoppages = detect_stoppages(meta, [], commentary)
    types = {s["stoppage_type"] for s in stoppages}
    assert "hydration" in types
    assert "var" in types  # commentary-derived VAR (no incidents needed)
    assert any(t.startswith("injury") for t in types)
