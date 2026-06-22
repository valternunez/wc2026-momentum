"""Generate a SYNTHETIC match fixture mirroring SofaScore's real JSON shapes.

This is NOT real match data. It exists so the parse -> features -> pipeline ->
report chain can be developed and unit-tested fully offline (CLAUDE.md: commit a
one-match fixture so the pipeline is testable without network). The JSON shapes
(graphPoints / incidents / event / commentary) match the live API so the same
parsers work on real data.

Designed signals (so tests can assert on them):
  - hydration break clustered around 22' and 67'
  - VAR decision at 40'
  - injury at 55' WITH a sub at 56'  -> injury_huddle
  - injury at 75' WITHOUT a sub      -> injury_no_huddle
  - momentum: home dominant before each hydration break, drops after
    (lets us check momentum_delta sign for the team that was on top)

Run:  uv run python tests/generate_synthetic_fixture.py
"""

from __future__ import annotations

import json
from pathlib import Path

MATCH_ID = 9999001
OUT = Path(__file__).resolve().parent / "fixtures" / "synthetic_match"


def momentum_value(minute: float) -> float:
    """Home-positive momentum. Strong home pressure that collapses right after
    each hydration break (22', 67') — the 'momentum killer' pattern to detect."""
    if minute < 22:  # building home pressure into the first break
        v = 10 + minute  # ~ +10..+31
    elif minute < 27:  # right after the break: swings to the away team
        v = -15
    elif minute < 67:
        v = 8  # mild home edge mid-game
    elif minute < 72:  # after the second break: away again
        v = -18
    else:
        v = 5
    # tiny deterministic wobble so slopes aren't perfectly flat
    return round(v + (minute % 3) - 1, 2)


def build_graph() -> dict:
    points = [{"minute": float(m), "value": momentum_value(m)} for m in range(1, 96)]
    # a couple of fractional stoppage-time points, as the real API returns
    points.append({"minute": 45.5, "value": momentum_value(45)})
    points.append({"minute": 90.5, "value": momentum_value(90)})
    return {"graphPoints": points}


def build_incidents() -> dict:
    # SofaScore returns newest-first; our parser re-sorts chronologically.
    incidents = [
        {"incidentType": "goal", "time": 30, "isHome": True, "homeScore": 1, "awayScore": 0,
         "incidentClass": "regular"},
        {"incidentType": "card", "time": 35, "isHome": False, "incidentClass": "yellow"},
        {"incidentType": "varDecision", "time": 40, "isHome": True, "incidentClass": "penaltyNotAwarded"},
        {"incidentType": "substitution", "time": 56, "isHome": True,
         "playerIn": {"name": "Sub A"}, "playerOut": {"name": "Starter A"}},
        {"incidentType": "substitution", "time": 70, "isHome": False,
         "playerIn": {"name": "Sub B"}, "playerOut": {"name": "Starter B"}},
        {"incidentType": "card", "time": 82, "isHome": True, "incidentClass": "red"},
        {"incidentType": "injuryTime", "time": 45, "length": 2},
        {"incidentType": "period", "time": 45, "text": "HT"},
    ]
    incidents.reverse()  # mimic newest-first ordering
    return {"incidents": incidents}


def build_event() -> dict:
    return {
        "event": {
            "id": MATCH_ID,
            "startTimestamp": 1781000000,  # 2026-06-09 (synthetic)
            "homeTeam": {"id": 1001, "name": "Testland"},
            "awayTeam": {"id": 1002, "name": "Mockovia"},
            "tournament": {"name": "Synthetic WC 2026"},
            "roundInfo": {"name": "Group A"},
            "venue": {"city": {"name": "Testville"}, "stadium": {"name": "Fixture Arena"}},
            "homeScore": {"current": 1},
            "awayScore": {"current": 0},
        }
    }


def build_commentary() -> list[dict]:
    # Normalized commentary (already in our internal shape, minute as "MM'").
    return [
        {"minute": "21'", "text": "The referee signals a cooling break; players take on drinks."},
        {"minute": "22'", "text": "Hydration break over, we're back underway."},
        {"minute": "40'", "text": "VAR is checking a possible penalty for Testland."},
        {"minute": "55'", "text": "Player down injured, receiving treatment from the physio."},
        {"minute": "66'", "text": "Another drinks break as temperatures soar in Testville."},
        {"minute": "75'", "text": "Injury concern — a knock requires treatment on the pitch."},
        {"minute": "80'", "text": "A lovely passing move ends with a shot over the bar."},
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "graph.json").write_text(json.dumps(build_graph(), indent=0), encoding="utf-8")
    (OUT / "incidents.json").write_text(json.dumps(build_incidents(), indent=0), encoding="utf-8")
    (OUT / "event.json").write_text(json.dumps(build_event(), indent=0), encoding="utf-8")
    (OUT / "commentary.json").write_text(json.dumps(build_commentary(), indent=0), encoding="utf-8")
    print(f"wrote synthetic fixture to {OUT}")


if __name__ == "__main__":
    main()
