"""Discover World Cup 2026 SofaScore event ids from the daily schedule.

Serves two needs: (1) getting a real event id to prove the live scrape works
(#1), and (2) seeding `data/match_ids.json` for the daily runner (#4). Runs from a
residential IP like the rest of the scrape (datacenter IPs get Cloudflare-challenged).

Endpoint: /api/v1/sport/football/scheduled-events/{YYYY-MM-DD} -> {"events": [...]}.
We filter to the FIFA World Cup. SofaScore's uniqueTournament id for the World Cup
is 16; we match on that OR a "world cup" name substring as a fallback.
"""

from __future__ import annotations

import json
from typing import Any

from src.paths import RAW
from src.scrape.sofascore import API, _get_json, make_client

WORLD_CUP_UT_ID = 16  # SofaScore uniqueTournament id for the FIFA World Cup
RAW_SCHEDULE = RAW / "schedule"


def _is_world_cup(event: dict[str, Any]) -> bool:
    tour = event.get("tournament") or {}
    ut = (tour.get("uniqueTournament") or {})
    if ut.get("id") == WORLD_CUP_UT_ID:
        return True
    name = f"{tour.get('name', '')} {ut.get('name', '')}".lower()
    return "world cup" in name


def fetch_scheduled(date_str: str, *, client=None) -> dict[str, Any]:
    """Fetch + persist the raw schedule for a date (YYYY-MM-DD). Idempotent."""
    RAW_SCHEDULE.mkdir(parents=True, exist_ok=True)
    path = RAW_SCHEDULE / f"{date_str}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    client = client or make_client()
    data = _get_json(client, f"{API}/sport/football/scheduled-events/{date_str}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
    return data


def list_wc_events(date_str: str, *, client=None) -> list[dict[str, Any]]:
    """World Cup events on a date as [{id, home, away, start_timestamp, status}]."""
    data = fetch_scheduled(date_str, client=client)
    out = []
    for ev in data.get("events", []) or []:
        if not _is_world_cup(ev):
            continue
        out.append(
            {
                "id": ev.get("id"),
                "home": (ev.get("homeTeam") or {}).get("name"),
                "away": (ev.get("awayTeam") or {}).get("name"),
                "start_timestamp": ev.get("startTimestamp"),
                "status": (ev.get("status") or {}).get("type"),
            }
        )
    return out


def list_wc_event_ids(date_str: str, *, client=None) -> list[int]:
    """Just the World Cup event ids on a date (convenience for seeding match_ids)."""
    return [e["id"] for e in list_wc_events(date_str, client=client) if e["id"] is not None]


def main() -> None:
    import sys

    dates = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not dates:
        print("usage: python -m src.scrape.schedule YYYY-MM-DD [...] [--browser|--curl] [--headless]")
        raise SystemExit(2)
    # Default: reuse Chrome's Cloudflare clearance (cookies). --browser / --curl override.
    use_browser = "--browser" in flags
    use_curl = "--curl" in flags
    client = make_client(
        use_cookies=not (use_browser or use_curl),
        use_browser=use_browser,
        headless="--headless" in flags,
    )
    try:
        all_ids: list[int] = []
        for date_str in dates:
            events = list_wc_events(date_str, client=client)
            print(f"\n{date_str}: {len(events)} World Cup match(es)")
            for e in events:
                print(f"  {e['id']}  {e['home']} vs {e['away']}  [{e['status']}]")
            all_ids += [e["id"] for e in events if e["id"]]
        if all_ids:
            print(f"\nevent ids: {json.dumps(sorted(set(all_ids)))}")
    finally:
        if hasattr(client, "close"):
            client.close()


if __name__ == "__main__":
    main()
