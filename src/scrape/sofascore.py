"""SofaScore scraper — primary momentum + incidents source.

SofaScore sits behind Cloudflare. Plain `httpx`/`requests` get a 403 "challenge"
from datacenter IPs. The reliable approach is `curl_cffi` impersonating a real
Chrome TLS fingerprint, run from a residential IP (hence: scrape locally, never
in CI — see CLAUDE.md). Even then, expect occasional challenges; we retry.

Discipline (CLAUDE.md): **persist raw JSON before any parsing**, and never
re-fetch a match whose raw files already exist. The pipeline reads from disk.

Endpoints (internal API used by the web app):
  /api/v1/event/{id}            -> match metadata
  /api/v1/event/{id}/graph      -> per-minute momentum ("graphPoints")
  /api/v1/event/{id}/incidents  -> goals, cards, subs, periods, VAR, injury time
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.paths import RAW_SOFASCORE

API = "https://api.sofascore.com/api/v1"

# Endpoint name -> URL suffix. Persisted as data/raw/sofascore/<id>/<name>.json
ENDPOINTS = {
    "event": "/event/{id}",
    "graph": "/event/{id}/graph",
    "incidents": "/event/{id}/incidents",
}


def make_client(*, use_cookies: bool = False, use_browser: bool = False, headless: bool = False):
    """Return a fetch client for SofaScore.

    Three strategies (all expose `.get(url) -> resp(.status_code/.text/.json())`):
    * `use_cookies=True` (default for scraping) — curl_cffi preloaded with the
      `cf_clearance` cookie from your real Chrome (see cookies.py). SofaScore's
      Cloudflare hard-blocks automated browsers, so reusing your human browser's
      clearance is the reliable path.
    * `use_browser=True` — Playwright `BrowserSession` (browser.py); usually blocked
      by CF bot-management, kept as a fallback.
    * neither — plain curl_cffi impersonation (will 403; only to reconfirm the block).
    Imported lazily so parse/features/report don't need these deps.
    """
    if use_cookies:
        from src.scrape.cookies import make_cookie_client

        return make_cookie_client()

    if use_browser:
        from src.scrape.browser import BrowserSession

        return BrowserSession(headless=headless)

    from curl_cffi import requests as creq

    sess = creq.Session(impersonate="chrome131")
    sess.headers.update(
        {
            "Accept": "application/json",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
        }
    )
    return sess


def _get_json(client, url: str, *, retries: int = 4, backoff: float = 2.0) -> dict[str, Any]:
    last = None
    for attempt in range(retries):
        resp = client.get(url, timeout=25)
        if resp.status_code == 200:
            return resp.json()
        last = f"{resp.status_code} {resp.text[:120]}"
        # 403 challenge / 429 rate limit -> wait and retry
        time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url} :: {last}")


def fetch_match(match_id: int | str, *, client=None, force: bool = False) -> dict[str, Any]:
    """Fetch + persist raw JSON for one match. Idempotent.

    Returns {endpoint_name: parsed_json}. If all raw files already exist and
    `force` is False, reads them from disk and makes NO network calls.
    """
    out_dir = RAW_SOFASCORE / str(match_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw: dict[str, Any] = {}
    need_network = force or any(not (out_dir / f"{n}.json").exists() for n in ENDPOINTS)

    if need_network and client is None:
        client = make_client()

    for name, suffix in ENDPOINTS.items():
        path = out_dir / f"{name}.json"
        if path.exists() and not force:
            raw[name] = json.loads(path.read_text(encoding="utf-8"))
            continue
        data = _get_json(client, API + suffix.format(id=match_id))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
        raw[name] = data
        time.sleep(1.0)  # be polite between endpoints
    return raw


def load_raw(match_id: int | str) -> dict[str, Any]:
    """Read already-persisted raw JSON for a match (no network). For analysis."""
    out_dir = RAW_SOFASCORE / str(match_id)
    return {
        name: json.loads((out_dir / f"{name}.json").read_text(encoding="utf-8"))
        for name in ENDPOINTS
        if (out_dir / f"{name}.json").exists()
    }


# --- Pure parsers over the raw JSON (no network) ----------------------------
# These define the shapes the downstream pipeline depends on. They are exercised
# offline by the test fixtures, so they double as the schema contract.


def parse_momentum(graph_json: dict[str, Any]) -> list[dict[str, float]]:
    """Per-minute momentum series. Convention: value > 0 = home, < 0 = away.

    SofaScore returns {"graphPoints": [{"minute": 1.0, "value": 12.3}, ...]}.
    Minute may be fractional (e.g. 45.5 for first-half stoppage time).
    """
    points = graph_json.get("graphPoints", []) or []
    return [
        {"minute": float(p["minute"]), "value": float(p["value"])}
        for p in points
        if p.get("minute") is not None and p.get("value") is not None
    ]


def parse_match_meta(event_json: dict[str, Any]) -> dict[str, Any]:
    """Flatten the fields we need from /event/{id}."""
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


def parse_incidents(incidents_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize SofaScore incidents into a flat, source-agnostic list.

    Each row: {kind, minute, added, is_home, detail, home_score, away_score, raw_type}.
    `kind` in {goal, card, substitution, var, injury_time, period, other}.
    Note: SofaScore does NOT emit hydration/cooling breaks here — those come from
    the commentary feed (see scrape/commentary.py).
    """
    out: list[dict[str, Any]] = []
    for inc in incidents_json.get("incidents", []) or []:
        itype = inc.get("incidentType")
        kind = {
            "goal": "goal",
            "card": "card",
            "substitution": "substitution",
            "varDecision": "var",
            "injuryTime": "injury_time",
            "period": "period",
        }.get(itype, "other")
        out.append(
            {
                "kind": kind,
                "raw_type": itype,
                "minute": inc.get("time"),
                "added": inc.get("addedTime"),
                "is_home": inc.get("isHome"),
                "detail": inc.get("incidentClass") or inc.get("text"),
                "length": inc.get("length"),  # injuryTime length (minutes)
                "home_score": inc.get("homeScore"),
                "away_score": inc.get("awayScore"),
            }
        )
    # SofaScore lists incidents newest-first; return chronological.
    out.sort(key=lambda r: (r["minute"] if r["minute"] is not None else 1e9, r.get("added") or 0))
    return out


def _diagnostic(
    match_id: str, *, use_cookies: bool = True, use_browser: bool = False, headless: bool = False
) -> int:
    """Fetch one match and print a health summary. Returns a process exit code.

    The one-command proof that the live scrape works (#1). Defaults to the cookie
    client (reuses your Chrome's Cloudflare clearance). Exercises fetch -> parse
    -> detect end to end.
    """
    from src.parse.stoppages import detect_stoppages
    from src.scrape import commentary as comm

    print(f"[diag] fetching SofaScore event {match_id} (cookies={use_cookies}, browser={use_browser}) …")
    client = make_client(use_cookies=use_cookies, use_browser=use_browser, headless=headless)
    try:
        raw = fetch_match(match_id, client=client, force=True)
    except Exception as e:
        print(f"[diag] FAIL: {type(e).__name__}: {e}")
        print("[diag] if this is a 403 'challenge', try the browser path and see the")
        print("       'Prove the scrape' runbook in reports/automation.md.")
        return 1
    finally:
        if hasattr(client, "close"):
            client.close()

    meta = parse_match_meta(raw["event"])
    momentum = parse_momentum(raw["graph"])
    incidents = parse_incidents(raw.get("incidents", {}))
    fot = comm.fetch_fotmob_commentary(match_id)
    commentary = comm.normalize_lines(fot) if fot else []
    stoppages = detect_stoppages(meta, incidents, commentary)

    print(f"[diag] OK  {meta.get('home_team')} {meta.get('home_score')}–"
          f"{meta.get('away_score')} {meta.get('away_team')}  ({meta.get('stage')})")
    print(f"[diag] momentum points: {len(momentum)}")
    print(f"[diag] incidents:       {len(incidents)}")
    print(f"[diag] commentary lines:{len(commentary)} (FotMob)")
    print(f"[diag] stoppages detected: {len(stoppages)} "
          f"-> {sorted({s['stoppage_type'] for s in stoppages})}")
    if not momentum:
        print("[diag] WARNING: empty momentum series — match may be unstarted or shape changed.")
        return 1
    if not commentary:
        print("[diag] note: no FotMob commentary — hydration breaks rely on it; "
              "BBC/ESPN adapters (commentary_sources.py) can supplement.")
    return 0


if __name__ == "__main__":
    import sys

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) != 1:
        print("usage: python -m src.scrape.sofascore <event_id> [--browser|--curl] [--headless]")
        raise SystemExit(2)
    use_browser = "--browser" in flags
    use_curl = "--curl" in flags
    raise SystemExit(
        _diagnostic(
            args[0],
            use_cookies=not (use_browser or use_curl),
            use_browser=use_browser,
            headless="--headless" in flags,
        )
    )
