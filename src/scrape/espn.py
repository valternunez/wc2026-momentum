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
import unicodedata
from datetime import datetime, timedelta
from typing import Any

from src.paths import RAW
from src.scrape.commentary import normalize_lines

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
WORLD_CUP_LEAGUE = "fifa.world"
RAW_ESPN = RAW / "espn"

# Tokens to drop before comparing team names.
_STOPWORDS = {"and", "of", "the"}
# Known FotMob<->ESPN name divergences (fold-no-space key -> canonical token).
_ALIAS = {
    "unitedstates": "usa", "usa": "usa",
    "korearepublic": "korea", "southkorea": "korea",
    "cotedivoire": "ivc", "ivorycoast": "ivc",
    "czechrepublic": "czech", "czechia": "czech",
    "turkiye": "turkey",
    "caboverde": "capeverde",
}


def _client(client=None):
    if client is not None:
        return client
    from curl_cffi import requests as creq

    return creq.Session(impersonate="chrome131")


def _fold(name: str | None) -> str:
    """Accent-fold to ASCII, lowercase, non-alphanumerics -> spaces."""
    ascii_ = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_.lower()).strip()


def canon(name: str | None) -> str:
    """Canonical team token, robust to accents, word order, hyphens, and aliases.

    e.g. "DR Congo"=="Congo DR", "Bosnia and Herzegovina"=="Bosnia-Herzegovina",
    "Curaçao"=="Curacao", "USA"=="United States", "Korea Republic"=="South Korea".
    """
    folded = _fold(name)
    nospace = folded.replace(" ", "")
    if nospace in _ALIAS:
        return _ALIAS[nospace]
    return "".join(sorted(t for t in folded.split() if t not in _STOPWORDS))


# Back-compat alias used by older call sites/tests.
def _norm(name: str | None) -> str:
    return _fold(name).replace(" ", "")


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


def _teams_match(home1: str, away1: str, home2: str, away2: str) -> bool:
    """True if two fixtures are the same pair of teams (order-independent, canonicalised)."""
    return {canon(home1), canon(away1)} == {canon(home2), canon(away2)}


def _shift_date(date_str: str, days: int) -> str:
    return (datetime.strptime(date_str, "%Y%m%d") + timedelta(days=days)).strftime("%Y%m%d")


def find_event_id(date_str: str, home: str, away: str, *, league: str = WORLD_CUP_LEAGUE, client=None):
    """Match a FotMob (home, away) to an ESPN event id, searching date ±1 day.

    FotMob's UTC match date and ESPN's scoreboard date can differ by a day, so we
    check the day before/after too. The same (home, away) pair within a 3-day window
    is effectively unique in a WC group stage, so this won't cross-match.
    """
    client = _client(client)
    for offset in (0, -1, 1):
        for e in scoreboard(_shift_date(date_str, offset), league=league, client=client):
            if _teams_match(home, away, e["home"], e["away"]):
                return e["id"]
    return None


def parse_commentary(summary_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Raw ESPN summary -> pre-normalized commentary lines.

    Each line: {minute, text, seconds, delay, wallclock}. ESPN tags a stoppage with a
    "Start Delay" / "End Delay" play (`play.type.text`) and carries a match-clock second value
    (`play.clock.value`, e.g. 1335.0) plus an ISO wall-clock (`play.wallclock`). Pairing a
    hydration Start Delay with the next End Delay gives the exact break duration in seconds
    (the match clock runs through stoppages, so the delta is real elapsed time, immune to the
    posting lag a wall-clock would carry). We keep all three; downstream uses `seconds`.
    """
    out = []
    for c in summary_json.get("commentary") or []:
        play = c.get("play") or {}
        ptype = ((play.get("type") or {}).get("text") or "").lower()
        delay = "start" if "start delay" in ptype else ("end" if "end delay" in ptype else None)
        secs = (play.get("clock") or {}).get("value")
        if secs is None:
            secs = (c.get("time") or {}).get("value")
        out.append({
            "minute": (c.get("time") or {}).get("displayValue"),
            "text": c.get("text"),
            "seconds": float(secs) if secs is not None else None,
            "delay": delay,
            "wallclock": play.get("wallclock"),
        })
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
