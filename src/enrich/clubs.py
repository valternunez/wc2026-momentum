"""Club -> recent home thermal load (the acclimatization reference).

`club_home_wbgt(team_id, window)` resolves a club's home stadium coordinates (FotMob team
endpoint, cached) and returns the mean WBGT at its home over the pre-tournament run-in window
— i.e. roughly what the players' bodies were adapted to before flying in. One ranged
Open-Meteo call per (club, window), cached. Returns None on any failure (missing coords,
unknown club) so callers degrade gracefully.

Acclimatization is about *recent* exposure, so the window is the ~7 weeks ending a week before
the tournament — not a multi-year normal.
"""

from __future__ import annotations

from datetime import date, timedelta

from src.enrich.weather import climate_mean_wbgt
from src.scrape.fotmob_clubs import fetch_team, team_home_coords


def pre_tournament_window(tournament_start: date, *, weeks: int = 7, lead_days: int = 7) -> tuple[str, str]:
    """[start, end] ISO dates for the run-in ending `lead_days` before the tournament."""
    end = tournament_start - timedelta(days=lead_days)
    start = end - timedelta(weeks=weeks)
    return start.isoformat(), end.isoformat()


def club_home_wbgt(
    team_id: int | str, window: tuple[str, str], *, client=None, weather_client=None
) -> float | None:
    """Mean home-stadium WBGT for a club over `window` (ISO start, end). None if unresolved."""
    if team_id is None:
        return None
    try:
        coords = team_home_coords(fetch_team(team_id, client=client))
    except Exception:
        return None
    if not coords:
        return None
    lat, lon = coords
    try:
        return climate_mean_wbgt(lat, lon, window[0], window[1], client=weather_client)
    except Exception:
        return None
