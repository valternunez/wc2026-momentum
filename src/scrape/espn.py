"""ESPN commentary — timestamped play-by-play to augment FotMob (which has none).

FotMob gives the momentum series but no commentary/VAR, so hydration breaks could
only be marked at nominal minutes. ESPN's hidden site API is open (no auth) and
carries minute-by-minute commentary — including cooling/hydration breaks, VAR
reviews, and injuries — the text our classifier turns into stoppages.

We discover the ESPN event by date + team names (FotMob has no ESPN id), then fetch
its commentary. Men's World Cup league slug = 'fifa.world'. Best-effort: every
function degrades to [] so a missing/renamed ESPN match never breaks the FotMob run.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.paths import RAW
from src.scrape.commentary import normalize_lines

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
WORLD_CUP_LEAGUE = "fifa.world"
RAW_ESPN = RAW / "espn"


def _client(client=None):
    if client is not None:
        return client
    from curl_cffi import requests as creq

    return creq.Session(impersonate="chrome131")


def _norm(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def scoreboard(date_str: str, *, league: str = WORLD_CUP_LEAGUE, client=None) -> list[dict[str, Any]]:
    """World Cup events on a date (date_str = 'YYYYMMDD'). [] on failure."""
    try:
        r = _client(client).get(f"{ESPN}/{league}/scoreboard?dates={date_str}", timeout=25)
        if r.status_code != 200:
            return []
        out = []
        for ev in r.json().get("events", []) or []:
            comp = ((ev.get("competitions") or [{}])[0].get("competitors")) or []
            home = next((x["team"] for x in comp if x.get("homeAway") == "home"), {})
            away = next((x["team"] for x in comp if x.get("homeAway") == "away"), {})
            out.append({"id": ev.get("id"), "date": ev.get("date"),
                        "home": home.get("displayName"), "away": away.get("displayName")})
        return out
    except Exception:
        return []


def _teams_match(want: set[str], got: set[str]) -> bool:
    if want == got:
        return True
    # tolerant substring match for naming differences (USA vs United States, etc.)
    return all(any(w and (w in g or g in w) for g in got) for w in want if w)


def find_event_id(date_str: str, home: str, away: str, *, league: str = WORLD_CUP_LEAGUE, client=None):
    """Match a FotMob (home, away) on a date to an ESPN event id by team names."""
    want = {_norm(home), _norm(away)}
    for e in scoreboard(date_str, league=league, client=client):
        if _teams_match(want, {_norm(e["home"]), _norm(e["away"])}):
            return e["id"]
    return None


def parse_commentary(summary_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Raw ESPN summary -> pre-normalized commentary lines [{minute, text}]."""
    out = []
    for c in summary_json.get("commentary") or []:
        out.append({"minute": (c.get("time") or {}).get("displayValue"), "text": c.get("text")})
    return out


def fetch_commentary(event_id: str | int, *, league: str = WORLD_CUP_LEAGUE, client=None, force: bool = False):
    """Fetch + persist an ESPN summary; return normalized+classified commentary lines."""
    RAW_ESPN.mkdir(parents=True, exist_ok=True)
    path = RAW_ESPN / f"{event_id}.json"
    if path.exists() and not force:
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        try:
            r = _client(client).get(f"{ESPN}/{league}/summary?event={event_id}", timeout=25)
            if r.status_code != 200:
                return []
            data = r.json()
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            return []
    return normalize_lines(parse_commentary(data))


def commentary_for_match(date_str: str, home: str, away: str, *, league: str = WORLD_CUP_LEAGUE, client=None):
    """One call: discover the ESPN event for (date, teams) and return its commentary."""
    c = _client(client)
    eid = find_event_id(date_str, home, away, league=league, client=c)
    return fetch_commentary(eid, league=league, client=c) if eid else []
