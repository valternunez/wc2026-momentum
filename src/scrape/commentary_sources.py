"""Per-provider commentary adapters: BBC Sport + ESPN.

The brief wants commentary reconciled across >=2 sources to detect stoppages that
SofaScore's incident feed misses (esp. hydration/cooling breaks). `commentary.py`
already covers FotMob; this module adds BBC Sport and ESPN so `reconcile.py` has
multiple feeds to cross-check.

Each provider gets two functions:

  fetch_<src>(...)  -> normalized lines, best-effort network. Persists the raw
                       page/JSON under data/raw/commentary/ BEFORE parsing, and
                       degrades to [] on ANY failure so the pipeline never breaks
                       when a source is unavailable. These run from a residential
                       IP and are not verifiable in CI.

  parse_<src>(raw)  -> PURE function: raw page/JSON -> pre-normalized line shape
                       [{"minute": ..., "text": ...}]. This is the tested part.

Both fetchers finish by handing parsed lines to `normalize_lines` (from
commentary.py) so every source emits the canonical
[{"minute": float|None, "text": str, "type": str}] shape.
"""

from __future__ import annotations

import json
import re
from typing import Any

from selectolax.parser import HTMLParser

from src.paths import RAW_COMMENTARY
from src.scrape.commentary import normalize_lines

# --- shared helpers ---------------------------------------------------------

# BBC live-text minute labels look like "22'", "45+2'", "HT", "FT". We only keep
# numeric (incl. stoppage-time) markers; non-numeric labels -> minute None.
_MINUTE_RE = re.compile(r"\d+\s*(?:\+\s*\d+)?\s*'?")


def _raw_path(match_id: int | str, source: str, ext: str):
    RAW_COMMENTARY.mkdir(parents=True, exist_ok=True)
    return RAW_COMMENTARY / f"{match_id}.{source}.{ext}"


def _clean(text: str | None) -> str:
    """Collapse whitespace in a commentary body."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _minute_token(label: str | None) -> str | None:
    """Pull the bare minute token (e.g. '90+2') out of a noisy time label.

    Returns a string that `commentary._coerce_minute` understands, or None for
    non-numeric markers like 'HT'/'FT'/'Live'.
    """
    if not label:
        return None
    m = _MINUTE_RE.search(label)
    if not m:
        return None
    return m.group(0).replace("'", "").replace(" ", "")


# --- BBC Sport --------------------------------------------------------------


def parse_bbc(html: str) -> list[dict[str, Any]]:
    """Parse BBC Sport live-text HTML into pre-normalized commentary lines.

    PURE. BBC renders each post as a stream item carrying a minute/time label and
    a text body. We are defensive about class names (BBC reshuffles them) by
    matching on the stable prefixes `lx-stream-post`, falling back to list items.
    """
    if not html:
        return []
    tree = HTMLParser(html)
    posts = tree.css("article.lx-stream-post") or tree.css(".lx-stream-post") or tree.css("li.lx-stream-post")
    lines: list[dict[str, Any]] = []
    for post in posts:
        time_node = (
            post.css_first(".lx-stream-post__meta-time")
            or post.css_first("[class*=meta-time]")
            or post.css_first("time")
        )
        body_node = (
            post.css_first(".lx-stream-post__body")
            or post.css_first("[class*=stream-post__body]")
            or post
        )
        label = time_node.text(strip=True) if time_node else None
        text = _clean(body_node.text(separator=" ")) if body_node else ""
        if not text:
            continue
        lines.append({"minute": _minute_token(label), "text": text})
    return lines


def fetch_bbc_commentary(url: str, match_id: int | str, *, client=None) -> list[dict[str, Any]]:
    """Best-effort: fetch a BBC Sport live-text page, persist raw HTML, parse.

    `url` is the match's live-text URL (BBC ids are slugs, not numeric, so the
    caller supplies the URL and a `match_id` we cache under). Returns [] on any
    failure. BBC may block datacentre IPs -> impersonate a real browser.
    """
    try:
        from curl_cffi import requests as creq

        c = client or creq.Session(impersonate="chrome120")
        r = c.get(url, timeout=25)
        if r.status_code != 200:
            return []
        html = r.text
        _raw_path(match_id, "bbc", "html").write_text(html, encoding="utf-8")
        return normalize_lines(parse_bbc(html))
    except Exception:
        return []


# --- ESPN -------------------------------------------------------------------


def parse_espn(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse ESPN summary/commentary JSON into pre-normalized commentary lines.

    PURE. ESPN nests timestamped lines under `commentary` (top level on the
    commentary endpoint, or under `gamepackageJSON` on the summary endpoint).
    Each item carries a `time.displayValue` like "22'" and a `text` body.
    """
    if not data:
        return []
    items = data.get("commentary")
    if items is None:
        pkg = data.get("gamepackageJSON") or {}
        items = pkg.get("commentary") or []
    lines: list[dict[str, Any]] = []
    for it in items or []:
        time_obj = it.get("time") or {}
        label = time_obj.get("displayValue") if isinstance(time_obj, dict) else time_obj
        play = it.get("play")
        raw_text = it.get("text") or (play.get("text") if isinstance(play, dict) else None)
        text = _clean(raw_text)
        if not text:
            continue
        lines.append({"minute": _minute_token(str(label) if label is not None else None), "text": text})
    return lines


def fetch_espn_commentary(event_id: int | str, *, client=None) -> list[dict[str, Any]]:
    """Best-effort: fetch ESPN soccer commentary JSON, persist raw, parse.

    Uses ESPN's public site API summary endpoint (carries a `commentary` block).
    Returns [] on any failure.
    """
    try:
        from curl_cffi import requests as creq

        c = client or creq.Session(impersonate="chrome120")
        url = (
            "https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary"
            f"?event={event_id}"
        )
        r = c.get(url, timeout=25)
        if r.status_code != 200:
            return []
        data = r.json()
        _raw_path(event_id, "espn", "json").write_text(
            json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8"
        )
        return normalize_lines(parse_espn(data))
    except Exception:
        return []
