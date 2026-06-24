"""FotMob team endpoint -> a club's home stadium coordinates (for the acclimatization study).

The match payloads give each national-team player's club (`primaryTeamId`); to turn that into a
home-city climate we need the club's home stadium location. FotMob's team endpoint
(`/api/data/teams?id=<id>`) carries it under `overview.venue.widget.location = [lat, lon]`
(with a JSON-LD GeoCoordinates fallback). Raw responses are persisted under
data/raw/fotmob_clubs/ (gitignored), idempotent per club id — CLAUDE.md: persist raw before use.

Network-only + LOCAL (residential IP), like the placebo scrapers; CI never calls this.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.paths import RAW
from src.scrape import fotmob

RAW_CLUBS = RAW / "fotmob_clubs"


def fetch_team(team_id: int | str, *, client=None, force: bool = False) -> dict[str, Any]:
    """Fetch + persist a FotMob team payload. Idempotent (reads disk unless force)."""
    RAW_CLUBS.mkdir(parents=True, exist_ok=True)
    path = RAW_CLUBS / f"{team_id}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    data = fotmob._get(client or fotmob.make_client(), f"/api/data/teams?id={team_id}")
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def team_home_coords(team_json: dict[str, Any]) -> tuple[float, float] | None:
    """(lat, lon) of the club's home stadium, or None if absent.

    Primary: overview.venue.widget.location = [lat, lon] (strings). Fallback: the first
    schema.org GeoCoordinates latitude/longitude pair anywhere in the payload.
    """
    widget = (((team_json.get("overview") or {}).get("venue") or {}).get("widget") or {})
    loc = widget.get("location")
    if isinstance(loc, (list, tuple)) and len(loc) == 2:
        try:
            return float(loc[0]), float(loc[1])
        except (TypeError, ValueError):
            pass
    blob = json.dumps(team_json)
    mlat = re.search(r'"latitude":\s*"?(-?\d+\.?\d*)"?', blob)
    mlon = re.search(r'"longitude":\s*"?(-?\d+\.?\d*)"?', blob)
    if mlat and mlon:
        try:
            return float(mlat.group(1)), float(mlon.group(1))
        except ValueError:
            pass
    return None


def team_home_name(team_json: dict[str, Any]) -> str | None:
    """Best-effort home stadium name (for logging/inspection)."""
    return (((team_json.get("overview") or {}).get("venue") or {}).get("widget") or {}).get("name")
