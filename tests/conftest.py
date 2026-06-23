"""Shared test fixtures.

The committed `synthetic_match` fixture is SofaScore-shaped (it predates the FotMob-only pivot)
and drives the required stoppage-detection + static-chart tests. SofaScore was removed from
`src/`, so the three pure (no-network) parsers it needs live here as the fixture's schema
contract. They are inlined (not a separate module) so pytest's conftest loader can use them
without package-relative imports.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from src.scrape import commentary as comm

FIX = Path(__file__).parent / "fixtures" / "synthetic_match"


def _read(name: str) -> dict | list:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _sofa_momentum(graph_json: dict[str, Any]) -> list[dict[str, float]]:
    points = graph_json.get("graphPoints", []) or []
    return [
        {"minute": float(p["minute"]), "value": float(p["value"])}
        for p in points
        if p.get("minute") is not None and p.get("value") is not None
    ]


def _sofa_meta(event_json: dict[str, Any]) -> dict[str, Any]:
    ev = event_json.get("event", event_json)
    venue = ev.get("venue") or {}
    stadium = venue.get("stadium") or {}
    round_info = ev.get("roundInfo") or {}
    return {
        "match_id": ev.get("id"),
        "start_timestamp": ev.get("startTimestamp"),
        "home_team": (ev.get("homeTeam") or {}).get("name"),
        "away_team": (ev.get("awayTeam") or {}).get("name"),
        "home_team_id": (ev.get("homeTeam") or {}).get("id"),
        "away_team_id": (ev.get("awayTeam") or {}).get("id"),
        "tournament": (ev.get("tournament") or {}).get("name"),
        "stage": round_info.get("name") or round_info.get("round"),
        "venue_city": (venue.get("city") or {}).get("name"),
        "venue_stadium": stadium.get("name"),
        "home_score": (ev.get("homeScore") or {}).get("current"),
        "away_score": (ev.get("awayScore") or {}).get("current"),
    }


def _sofa_incidents(incidents_json: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for inc in incidents_json.get("incidents", []) or []:
        itype = inc.get("incidentType")
        kind = {
            "goal": "goal", "card": "card", "substitution": "substitution",
            "varDecision": "var", "injuryTime": "injury_time", "period": "period",
        }.get(itype, "other")
        out.append({
            "kind": kind, "raw_type": itype, "minute": inc.get("time"),
            "added": inc.get("addedTime"), "is_home": inc.get("isHome"),
            "detail": inc.get("incidentClass") or inc.get("text"), "length": inc.get("length"),
            "home_score": inc.get("homeScore"), "away_score": inc.get("awayScore"),
        })
    out.sort(key=lambda r: (r["minute"] if r["minute"] is not None else 1e9, r.get("added") or 0))
    return out


@pytest.fixture
def match_inputs() -> dict:
    """Parsed synthetic-match inputs, via the pure parsers (offline)."""
    return {
        "meta": _sofa_meta(_read("event.json")),
        "momentum": _sofa_momentum(_read("graph.json")),
        "incidents": _sofa_incidents(_read("incidents.json")),
        "commentary": comm.normalize_lines(_read("commentary.json")),
    }
