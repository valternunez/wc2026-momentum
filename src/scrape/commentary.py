"""Commentary scraping + classification.

Hydration/cooling breaks are NOT in SofaScore's incident feed, so we detect them
from minute-by-minute commentary (the brief: detect from commentary, not a
hardcoded clock). Commentary providers differ (BBC, ESPN, FotMob), so we
normalize everything to a flat list of timestamped lines and run a single
keyword classifier over them.

Normalized commentary line: {"minute": float | None, "text": str, "type": str}
where `type` is one of the stoppage-signal labels from `classify_comment`, or
"none" for ordinary play-by-play.

The classifier is the part that must be correct and is unit-tested offline.
Network fetching is best-effort and must run from a residential IP.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.paths import RAW_COMMENTARY

# --- Classification ---------------------------------------------------------
# Order matters: first match wins. Hydration is checked before generic "break".

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "hydration",
        re.compile(
            r"\b(hydration|cooling|drinks?|water)\s+break\b|\bdrinks\s+(are\s+)?break|"
            r"\bbreak\s+for\s+(drinks|water|hydration)\b|\btaking on (fluids|water)\b|"
            r"\bdrinks are taken\b",
            re.IGNORECASE,
        ),
    ),
    (
        "var",
        re.compile(
            r"\bVAR\b|video\s+assistant|on[-\s]?field\s+review|checking\s+(for|the)|"
            r"\b(under|being)\s+review\b|review(ing)?\s+(a\s+)?(goal|penalty|red\s+card)|"
            r"\b(pitch[-\s]?side|the)\s+monitor\b|\bsent to the monitor\b",
            re.IGNORECASE,
        ),
    ),
    (
        "injury",
        re.compile(
            r"\b(injur(y|ed)|treatment|stretcher|physio|medical\s+staff|"
            r"down\s+(injured|in\s+pain)|receiving\s+treatment|knock)\b|"
            r"\bstays down\b|\bgoes down holding\b|\bneeds treatment\b",
            re.IGNORECASE,
        ),
    ),
    (
        "substitution",
        re.compile(r"\b(substitution|comes?\s+on\s+for|replaced\s+by|makes?\s+a\s+change)\b", re.IGNORECASE),
    ),
]


def classify_comment(text: str) -> str:
    """Map a commentary line to a stoppage-signal label, or 'none'.

    Returns one of: hydration | var | injury | substitution | none.
    (Injury is later refined into injury_huddle / injury_no_huddle in parse.)
    """
    if not text:
        return "none"
    for label, pat in _PATTERNS:
        if pat.search(text):
            return label
    return "none"


def normalize_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach a `type` to each raw commentary line via the classifier.

    Input lines must have at least `text`; `minute` is optional (float|None).
    """
    out = []
    for ln in lines:
        text = (ln.get("text") or "").strip()
        out.append(
            {
                "minute": _coerce_minute(ln.get("minute")),
                "text": text,
                "type": classify_comment(text),
            }
        )
    return out


def _coerce_minute(m: Any) -> float | None:
    if m is None:
        return None
    if isinstance(m, (int, float)):
        return float(m)
    # Commentary often gives "67'" or "90+2'"
    s = str(m).replace("'", "").strip()
    mm = re.match(r"^(\d+)(?:\+(\d+))?$", s)
    if not mm:
        return None
    base = int(mm.group(1))
    added = int(mm.group(2)) if mm.group(2) else 0
    return float(base + added)


# --- Persistence / fetch ----------------------------------------------------


def save_commentary(match_id: int | str, lines: list[dict[str, Any]]) -> None:
    """Persist normalized commentary (this IS our raw record for this source)."""
    RAW_COMMENTARY.mkdir(parents=True, exist_ok=True)
    path = RAW_COMMENTARY / f"{match_id}.json"
    path.write_text(json.dumps(lines, ensure_ascii=False, indent=0), encoding="utf-8")


def load_commentary(match_id: int | str) -> list[dict[str, Any]]:
    path = RAW_COMMENTARY / f"{match_id}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_fotmob_commentary(match_id: int | str, *, client=None) -> list[dict[str, Any]]:
    """Best-effort: pull commentary from FotMob's matchDetails and normalize.

    FotMob's payload shape shifts over time and may require a signed header from
    a residential session; this returns [] on any failure so the pipeline still
    runs from SofaScore + cached commentary. Run/validate from a home IP.
    """
    try:
        from curl_cffi import requests as creq

        c = client or creq.Session(impersonate="chrome131")
        url = f"https://www.fotmob.com/api/matchDetails?matchId={match_id}"
        r = c.get(url, timeout=25)
        if r.status_code != 200:
            return []
        data = r.json()
        raw_lines = _extract_fotmob_commentary(data)
        return normalize_lines(raw_lines)
    except Exception:
        return []


def _extract_fotmob_commentary(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Dig commentary lines out of FotMob's matchDetails JSON (defensive)."""
    content = data.get("content") or {}
    block = content.get("commentary") or content.get("liveticker") or {}
    items = block.get("commentary") or block.get("commentaryList") or []
    lines = []
    for it in items:
        lines.append({"minute": it.get("min") or it.get("minute"), "text": it.get("text") or it.get("comment")})
    return lines
