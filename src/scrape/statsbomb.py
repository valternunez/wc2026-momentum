"""StatsBomb Open Data loader — historical baseline & placebo (Phase 4/5).

Unlike SofaScore, StatsBomb open data is plain JSON on GitHub (no bot protection),
so this works from anywhere including CI. Used for:
  - a sanity check that our momentum metric tracks xT-flow on 2022 WC matches, and
  - a HISTORICAL PLACEBO: apply the same 22′/67′ windowing to 2022 WC matches,
    where no breaks were mandated — any "effect" there is bias (brief §Phase 3).

Computing an event-based momentum proxy (xT-flow via `socceraction`) is the next
analysis step and needs the `events` extra (`uv sync --extra events`); this module
provides the data access + match discovery that step builds on.

Competition ids: men's WC 2022 = competition 43 / season 106.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from src.paths import RAW

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
WC_2022 = {"competition_id": 43, "season_id": 106}
RAW_SB = RAW / "statsbomb"


def fetch_matches(competition_id: int = 43, season_id: int = 106) -> list[dict[str, Any]]:
    """Fetch + persist the match list for a competition/season. Idempotent."""
    RAW_SB.mkdir(parents=True, exist_ok=True)
    path = RAW_SB / f"matches_{competition_id}_{season_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    url = f"{BASE}/matches/{competition_id}/{season_id}.json"
    data = httpx.get(url, timeout=30, headers={"User-Agent": "wc2026-momentum"}).json()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
    return data


def fetch_events(match_id: int) -> list[dict[str, Any]]:
    """Fetch + persist event data for one StatsBomb match. Idempotent."""
    RAW_SB.mkdir(parents=True, exist_ok=True)
    path = RAW_SB / f"events_{match_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    url = f"{BASE}/events/{match_id}.json"
    data = httpx.get(url, timeout=60, headers={"User-Agent": "wc2026-momentum"}).json()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
    return data
