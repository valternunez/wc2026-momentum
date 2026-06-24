"""FotMob scraper — PRIMARY momentum source (SofaScore IP-blocks the user).

FotMob exposes a per-minute, home-positive momentum series plus structured events,
and — unlike SofaScore — does not Cloudflare-block us. Its `/api/data/*` endpoints
require an `x-mas` auth header: base64 of `{"body":{"url","code"},"signature"}`,
where `code` is a unix-ms timestamp and `signature = MD5(json(body) + SECRET)`
uppercased. `SECRET` is FotMob's easter-egg lyrics ("Three Lions"), stored verbatim
in `fotmob_secret_lyrics.txt` (byte-exact, including no trailing newline) — if FotMob
rotates it, replace that file.

Runtime is light: plain curl_cffi + the computed header. No browser, no cookie — good
for the unattended daily job.

Caveats vs SofaScore: FotMob matchDetails has NO commentary text and NO VAR/hydration
event types. So in FotMob mode we mark the mandatory WC2026 hydration breaks at their
nominal minutes (~22'/67'); exact-timing + VAR/injury detection needs the BBC/ESPN
commentary adapters (`commentary_sources.py`) layered on later.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from src.paths import HYDRATION_NOMINAL_MINUTES, RAW_FOTMOB, WINDOW_MIN

BASE = "https://www.fotmob.com"
_SECRET_PATH = Path(__file__).with_name("fotmob_secret_lyrics.txt")
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


# --- auth -------------------------------------------------------------------
def _secret() -> str:
    # Local: the gitignored file. Hosted (Railway): FOTMOB_SECRET_B64 (base64) or FOTMOB_SECRET env.
    if _SECRET_PATH.exists():
        return _SECRET_PATH.read_text(encoding="utf-8")
    b64 = os.environ.get("FOTMOB_SECRET_B64")
    if b64:
        return base64.b64decode(b64).decode("utf-8")
    env = os.environ.get("FOTMOB_SECRET")
    if env:
        return env
    raise RuntimeError(
        f"FotMob secret missing: provide {_SECRET_PATH.name} locally (gitignored, byte-exact "
        "easter-egg lyrics) or set FOTMOB_SECRET_B64 / FOTMOB_SECRET in the environment. Needed for "
        "scraping; CI/report builds and tests (which use fixtures) do not need it."
    )


def x_mas(api_path: str, *, code: int | None = None) -> str:
    """Build the FotMob `x-mas` header for an `/api/...` path (incl. query string).

    `code` (unix-ms) is injectable for deterministic tests.
    """
    code = int(time.time() * 1000) if code is None else code
    body = {"url": api_path, "code": code}
    payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    signature = hashlib.md5((payload + _secret()).encode("utf-8")).hexdigest().upper()
    token = json.dumps({"body": body, "signature": signature}, separators=(",", ":"))
    return base64.b64encode(token.encode("utf-8")).decode("ascii")


def make_client():
    """Plain curl_cffi session (FotMob needs no browser/cookie)."""
    from curl_cffi import requests as creq

    sess = creq.Session(impersonate="chrome131")
    sess.headers.update({"User-Agent": _UA, "Accept": "application/json"})
    return sess


def _get(client, api_path: str, *, retries: int = 3) -> dict[str, Any]:
    last = None
    for attempt in range(retries):
        r = client.get(BASE + api_path, headers={"x-mas": x_mas(api_path)}, timeout=25)
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                # 200 but not JSON — usually a Cloudflare interstitial HTML page. Don't keep retrying.
                ct = r.headers.get("content-type", "?")
                raise RuntimeError(f"FotMob 200 non-JSON ({ct}, {type(e).__name__}): {api_path}") from e
        # 4xx (other than 429 rate-limit) are auth/path errors that won't fix themselves — fail fast.
        if 400 <= r.status_code < 500 and r.status_code != 429:
            raise RuntimeError(f"FotMob GET {r.status_code}: {api_path}")
        last = str(r.status_code)  # log the status, not the body
        wait = 1.5 * (attempt + 1)
        ra = r.headers.get("Retry-After")
        if ra:
            try:
                wait = max(wait, float(ra))
            except ValueError:
                pass
        time.sleep(wait)
    raise RuntimeError(f"FotMob GET failed: {api_path} :: last status {last}")


# --- fetch / persist --------------------------------------------------------
def fetch_match_details(match_id: int | str, *, client=None, force: bool = False, dest_dir=None) -> dict[str, Any]:
    """Fetch + persist FotMob matchDetails. Idempotent (reads disk unless force).

    `dest_dir` defaults to RAW_FOTMOB (the WC2026 raw dir). Other competitions (e.g.
    CWC 2025) MUST pass a separate dir so the daily build doesn't ingest them as WC2026.
    """
    dest_dir = dest_dir or RAW_FOTMOB
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{match_id}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    data = _get(client or make_client(), f"/api/data/matchDetails?matchId={match_id}")
    # payload-shape guard: a gross schema change should fail loudly here, not silently parse to []
    missing = [k for k in ("general", "header", "content") if k not in data]
    if missing:
        raise RuntimeError(f"FotMob matchDetails {match_id}: unexpected payload shape, missing {missing}")
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def load_raw(match_id: int | str) -> dict[str, Any]:
    path = RAW_FOTMOB / f"{match_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


# --- discovery --------------------------------------------------------------
WORLD_CUP_PRIMARY_ID = 77  # FotMob primaryId for the men's FIFA World Cup


def list_competition_events(date_str: str, primary_id: int, *, client=None) -> list[dict[str, Any]]:
    """Matches for a competition (FotMob `primaryId`) on a date ('YYYYMMDD'). [] on none."""
    data = _get(client or make_client(), f"/api/data/matches?date={date_str}")
    out = []
    for lg in data.get("leagues", []) or []:
        if lg.get("primaryId") != primary_id and lg.get("parentLeagueId") != primary_id:
            continue
        for m in lg.get("matches", []) or []:
            out.append(
                {
                    "id": m.get("id"),
                    "home": (m.get("home") or {}).get("name"),
                    "away": (m.get("away") or {}).get("name"),
                    "status": (m.get("status") or {}).get("reason", {}).get("short")
                    or (m.get("status") or {}).get("utcTime"),
                }
            )
    return out


def list_wc_events(date_str: str, *, client=None) -> list[dict[str, Any]]:
    """Men's World Cup matches on a date (date_str = 'YYYYMMDD'). [] on none."""
    return list_competition_events(date_str, WORLD_CUP_PRIMARY_ID, client=client)


def list_wc_event_ids(date_str: str, *, client=None) -> list[int]:
    return [e["id"] for e in list_wc_events(date_str, client=client) if e["id"] is not None]


# --- parsers (match the shapes sofascore.parse_* produce) -------------------
def parse_momentum(details_json: dict[str, Any]) -> list[dict[str, float]]:
    """Per-minute momentum, home-positive (verified: positive skews to home)."""
    content = details_json.get("content") or {}
    main = (content.get("momentum") or {}).get("main") or {}
    out = []
    for p in main.get("data") or []:
        m, v = p.get("minute"), p.get("value")
        if m is not None and v is not None:
            out.append({"minute": float(m), "value": float(v)})
    return out


def parse_match_meta(details_json: dict[str, Any]) -> dict[str, Any]:
    g = details_json.get("general") or {}
    info = ((details_json.get("content") or {}).get("matchFacts") or {}).get("infoBox") or {}
    stadium = info.get("Stadium") or {}
    teams = (details_json.get("header") or {}).get("teams") or [{}, {}]
    return {
        "match_id": g.get("matchId"),
        "start_timestamp": _epoch(g.get("matchTimeUTCDate")),
        "home_team": (g.get("homeTeam") or {}).get("name"),
        "away_team": (g.get("awayTeam") or {}).get("name"),
        "home_team_id": (g.get("homeTeam") or {}).get("id"),
        "away_team_id": (g.get("awayTeam") or {}).get("id"),
        "tournament": g.get("leagueName"),
        "league_id": g.get("leagueId"),
        # the competition's parent: WC2026 group/knockout leagues all sit under primaryId 77, while
        # qualifiers (10195/…) and other tournaments (Euro 50, Copa 44) do not — used to gate the build.
        "parent_league_id": g.get("parentLeagueId"),
        "stage": g.get("leagueRoundName") or g.get("matchRound"),
        "venue_city": stadium.get("city"),
        "venue_stadium": stadium.get("name"),
        "home_score": teams[0].get("score") if len(teams) > 0 else None,
        "away_score": teams[1].get("score") if len(teams) > 1 else None,
    }


def parse_incidents(details_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize FotMob events to the same shape as sofascore.parse_incidents.

    FotMob events have no VAR/hydration types; we map goals, cards, subs.
    """
    mf = (details_json.get("content") or {}).get("matchFacts") or {}
    events = (mf.get("events") or {}).get("events") or []
    kind_map = {"Goal": "goal", "Card": "card", "Substitution": "substitution"}
    out: list[dict[str, Any]] = []
    for e in events:
        kind = kind_map.get(e.get("type"))
        if not kind:
            continue
        out.append(
            {
                "kind": kind,
                "raw_type": e.get("type"),
                "minute": e.get("time"),
                "added": e.get("overloadTime"),
                "is_home": e.get("isHome"),
                "detail": (e.get("card") or e.get("goalDescription") or "").lower() or None,
                "length": None,
                "home_score": e.get("homeScore"),
                "away_score": e.get("awayScore"),
            }
        )
    out.sort(key=lambda r: (r["minute"] if r["minute"] is not None else 1e9, r.get("added") or 0))
    return out


def parse_goals(details_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Compact goal/penalty timeline for the momentum chart markers.

    Each item: {m: minute, h: 1 if home scored else 0, who: scorer, sc: "H-A", k: kind}
    where kind is "" | "pen" | "og" | "header" | "fk" | "miss" (missed penalty, no score).
    Shootout entries are excluded (not part of in-match momentum).
    """
    mf = (details_json.get("content") or {}).get("matchFacts") or {}
    events = (mf.get("events") or {}).get("events") or []
    desc_map = {"penalty": "pen", "owngoal": "og", "header": "header", "direct_free_kick": "fk"}
    out: list[dict[str, Any]] = []
    for e in events:
        typ = e.get("type")
        if typ not in ("Goal", "MissedPenalty") or e.get("isPenaltyShootoutEvent"):
            continue
        if e.get("time") is None:
            continue
        who = e.get("nameStr") or (e.get("player") or {}).get("name") or ""
        if typ == "MissedPenalty":
            kind, sc = "miss", ""
        else:
            dkey = (e.get("goalDescriptionKey") or "").lower()
            kind = "og" if e.get("ownGoal") else desc_map.get(dkey, "")
            ns = e.get("newScore")
            sc = f"{ns[0]}-{ns[1]}" if isinstance(ns, (list, tuple)) and len(ns) == 2 else (str(ns) if ns else "")
        out.append({"m": int(e["time"]), "h": 1 if e.get("isHome") else 0, "who": who, "sc": sc, "k": kind})
    out.sort(key=lambda r: r["m"])
    return out


def parse_lineup(details_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-player lineup with club affiliation, from `content.lineup`.

    Each row: {player_id, name, side ('home'|'away'), is_starter, club_id, club_name}.
    `club_id`/`club_name` come from FotMob's `primaryTeamId`/`primaryTeamName` — the player's
    club at match time, which the acclimatization study maps to a home-city climate. These are
    present for recent national-team matches (WC2026/Copa24/Euro24) but ABSENT for some payloads
    (CWC 2025, WC 2022) — callers must tolerate club_id=None. Returns [] when no lineup exists.
    """
    lineup = (details_json.get("content") or {}).get("lineup") or {}
    out: list[dict[str, Any]] = []
    for side in ("home", "away"):
        team = lineup.get(f"{side}Team") or {}
        for group, is_starter in (("starters", True), ("subs", False)):
            for p in team.get(group) or []:
                out.append(
                    {
                        "player_id": p.get("id"),
                        "name": p.get("name"),
                        "side": side,
                        "is_starter": is_starter,
                        "club_id": p.get("primaryTeamId"),
                        "club_name": p.get("primaryTeamName"),
                    }
                )
    return out


def nominal_hydration_commentary(momentum: list[dict[str, float]]) -> list[dict[str, Any]]:
    """Synthetic hydration markers at nominal WC2026 minutes the match actually reached.

    FotMob has no commentary, so we mark the mandatory breaks at ~22'/67' (only if the
    match ran long enough to form a post-window). Returned pre-normalized so
    detect_stoppages picks them up exactly like real commentary.
    """
    if not momentum:
        return []
    max_min = max(p["minute"] for p in momentum)
    lines = []
    for mark in HYDRATION_NOMINAL_MINUTES:
        if max_min >= mark + WINDOW_MIN:
            lines.append(
                {"minute": float(mark), "text": "mandatory hydration break (nominal)", "type": "hydration"}
            )
    return lines


def match_inputs(match_id: int | str) -> tuple[dict, list, list, list]:
    """(meta, momentum, incidents, commentary) for one match, from persisted raw."""
    raw = load_raw(match_id)
    if not raw:
        return {}, [], [], []
    momentum = parse_momentum(raw)
    return parse_match_meta(raw), momentum, parse_incidents(raw), nominal_hydration_commentary(momentum)


def _epoch(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
    except Exception:
        return None


# --- cross-check (kept) -----------------------------------------------------
def correlation_with(sofa_series: list[dict[str, float]], fot_series: list[dict[str, float]]) -> float | None:
    """Pearson r between two momentum series on overlapping minutes (SofaScore vs FotMob)."""
    if not sofa_series or not fot_series:
        return None
    a = {round(p["minute"]): p["value"] for p in sofa_series}
    b = {round(p["minute"]): p["value"] for p in fot_series}
    common = sorted(set(a) & set(b))
    if len(common) < 3:
        return None
    import statistics

    try:
        return statistics.correlation([a[m] for m in common], [b[m] for m in common])
    except statistics.StatisticsError:
        return None


# --- diagnostic -------------------------------------------------------------
def _diagnostic(match_id: str) -> int:
    from src.parse.stoppages import detect_stoppages

    print(f"[diag] FotMob matchDetails {match_id} …")
    try:
        fetch_match_details(match_id, force=True)
    except Exception as e:
        print(f"[diag] FAIL: {type(e).__name__}: {e}")
        return 1
    meta, momentum, incidents, commentary = match_inputs(match_id)
    stoppages = detect_stoppages(meta, incidents, commentary)
    print(f"[diag] OK  {meta.get('home_team')} {meta.get('home_score')}–{meta.get('away_score')} "
          f"{meta.get('away_team')}  ({meta.get('stage')})")
    print(f"[diag] momentum points: {len(momentum)} | incidents: {len(incidents)}")
    print(f"[diag] stoppages: {len(stoppages)} -> {sorted({s['stoppage_type'] for s in stoppages})}")
    return 0 if momentum else 1


def _check_secret() -> int:
    """Reproduce the documented signature vector? (Note: that vector used FotMob's OLD
    secret, so a mismatch is expected with the current Three Lions secret — the real
    gate is a live 200.)"""
    sig = x_mas("/api/leagueseasondeepstats?id=67&season=22583&type=players&stat=expected_goals",
                code=1730380499852)
    print("[secret] header built OK; secret md5-len bytes:", len(_secret()))
    print("[secret] (live 200 from --diagnostic is the authoritative check)")
    return 0


def _list_date(date_str: str) -> int:
    client = make_client()
    events = list_wc_events(date_str, client=client)
    print(f"{date_str}: {len(events)} World Cup match(es)")
    for e in events:
        print(f"  {e['id']}  {e['home']} vs {e['away']}  [{e['status']}]")
    ids = [e["id"] for e in events if e["id"]]
    if ids:
        print(f"event ids: {json.dumps(sorted(set(ids)))}")
    return 0


if __name__ == "__main__":
    import sys

    if "--check-secret" in sys.argv:
        raise SystemExit(_check_secret())
    date = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--date=")), None)
    if date:
        raise SystemExit(_list_date(date))
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print("usage: python -m src.scrape.fotmob <match_id> | --date=YYYYMMDD | --check-secret")
        raise SystemExit(2)
    raise SystemExit(_diagnostic(args[0]))
