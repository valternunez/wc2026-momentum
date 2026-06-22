"""Tests for the FotMob source (primary momentum source). Offline against a real
(trimmed) matchDetails fixture: 2022 WC final, Argentina 3-3 France."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from src.features.momentum_features import COLUMNS
from src.parse.stoppages import detect_stoppages
from src.pipeline import assemble_rows
from src.scrape import fotmob

FIX = Path(__file__).parent / "fixtures" / "fotmob_match" / "matchDetails.json"
DETAILS = json.loads(FIX.read_text(encoding="utf-8"))


# --- auth header ------------------------------------------------------------
def test_x_mas_is_deterministic_and_well_formed():
    path = "/api/data/matchDetails?matchId=3370572"
    h1 = fotmob.x_mas(path, code=1730380499852)
    h2 = fotmob.x_mas(path, code=1730380499852)
    assert h1 == h2  # deterministic for a fixed code
    token = json.loads(base64.b64decode(h1))
    assert token["body"] == {"url": path, "code": 1730380499852}
    assert len(token["signature"]) == 32 and token["signature"].isupper()


def test_x_mas_changes_with_code():
    p = "/api/data/x"
    assert fotmob.x_mas(p, code=1) != fotmob.x_mas(p, code=2)


# --- parsers ----------------------------------------------------------------
def test_parse_meta():
    m = fotmob.parse_match_meta(DETAILS)
    assert m["home_team"] == "Argentina" and m["away_team"] == "France"
    assert m["home_score"] == 3 and m["away_score"] == 3
    assert m["stage"] == "final"
    assert "Lusail" in (m["venue_stadium"] or "")
    assert m["start_timestamp"] and m["start_timestamp"] > 1_600_000_000


def test_parse_momentum_home_positive():
    mom = fotmob.parse_momentum(DETAILS)
    assert len(mom) > 100
    assert all(isinstance(p["minute"], float) for p in mom)
    # Argentina (home) won; momentum should skew positive overall
    assert sum(p["value"] for p in mom) > 0


def test_parse_incidents_maps_types():
    inc = fotmob.parse_incidents(DETAILS)
    kinds = {i["kind"] for i in inc}
    assert {"goal", "card", "substitution"} <= kinds
    # goals carry running score + side
    goal = next(i for i in inc if i["kind"] == "goal")
    assert goal["is_home"] in (True, False)
    assert goal["home_score"] is not None


def test_nominal_hydration_markers():
    mom = fotmob.parse_momentum(DETAILS)
    lines = fotmob.nominal_hydration_commentary(mom)
    assert [round(x["minute"]) for x in lines] == [22, 67]
    assert all(x["type"] == "hydration" for x in lines)


# --- end to end (FotMob inputs -> existing pipeline) ------------------------
def test_assemble_rows_two_hydration_stoppages():
    meta = fotmob.parse_match_meta(DETAILS)
    mom = fotmob.parse_momentum(DETAILS)
    inc = fotmob.parse_incidents(DETAILS)
    comm = fotmob.nominal_hydration_commentary(mom)
    rows = assemble_rows(meta, mom, inc, comm)
    assert len(rows) == 4  # 2 hydration breaks x 2 team perspectives
    assert all(set(r.keys()) == set(COLUMNS) for r in rows)
    # mirrored perspectives sum to zero per stoppage
    by_stop: dict[str, float] = {}
    for r in rows:
        by_stop.setdefault(r["stoppage_id"], 0.0)
        by_stop[r["stoppage_id"]] += r["momentum_delta"]
    assert all(abs(v) < 1e-9 for v in by_stop.values())


def test_no_var_or_injury_from_fotmob_alone():
    # FotMob has no commentary/VAR types -> only hydration detected
    meta = fotmob.parse_match_meta(DETAILS)
    mom = fotmob.parse_momentum(DETAILS)
    inc = fotmob.parse_incidents(DETAILS)
    stoppages = detect_stoppages(meta, inc, fotmob.nominal_hydration_commentary(mom))
    assert {s["stoppage_type"] for s in stoppages} == {"hydration"}
