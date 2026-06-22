"""Reconcile normalized commentary across multiple providers into one feed.

The brief: detect stoppages (esp. hydration breaks, which SofaScore omits) more
robustly by cross-checking >=2 commentary sources (BBC Sport, ESPN, FotMob).
Different providers phrase and time the same event slightly differently, so a
naive concat double-counts breaks. `reconcile` merges them into a single
chronological, de-duplicated list:

  - events are duplicates if they share the same `type` AND fall within
    MINUTE_TOLERANCE minutes of each other;
  - on a duplicate we keep ONE event, preferring the richer (longer) text and
    a defined minute over a missing one;
  - all distinct events (different type, or far apart in time) are preserved.

Input: a list of per-source normalized line lists (output of `normalize_lines`).
Output: one merged normalized line list.

PURE — no I/O — so it is fully unit-tested offline.
"""

from __future__ import annotations

from typing import Any

# Two events of the same `type` within this many minutes are the same event.
# Providers disagree on the exact minute of a stoppage (one logs the whistle,
# another the resumption), so we allow a small window.
MINUTE_TOLERANCE = 2.0


# ---------------------------------------------------------------------------
# PROPOSED classifier patterns for the lead to merge into src/scrape/commentary.py
# (we do NOT edit that file; staged here as a constant for review). See the task
# summary for rationale. These cover phrasings the current _PATTERNS miss:
#   - "back on the monitor" / "checks the pitchside monitor" (VAR)
#   - "drinks are taken" / "taking on fluids" / "taking on water" (hydration)
#   - "goes down holding his" / "needs treatment" / "stays down" (injury)
PROPOSED_CLASSIFIER_PATTERNS: dict[str, list[str]] = {
    "hydration": [
        r"\btaking on (fluids|water)\b",
        r"\bdrinks are taken\b",
    ],
    "var": [
        r"\b(pitch[-\s]?side|the)\s+monitor\b",
        r"\bsent to the monitor\b",
    ],
    "injury": [
        r"\bstays down\b",
        r"\bgoes down holding\b",
        r"\bneeds treatment\b",
    ],
}


def reconcile(sources: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Merge normalized commentary from multiple sources into one feed.

    Args:
        sources: list of per-source normalized line lists. Each line is
            {"minute": float|None, "text": str, "type": str}.

    Returns:
        A single chronological, de-duplicated normalized line list. Lines with a
        minute sort before minute-less lines; ties keep first-seen order.
    """
    merged: list[dict[str, Any]] = []
    for src in sources:
        for line in src or []:
            existing = _find_duplicate(merged, line)
            if existing is None:
                merged.append(dict(line))
            else:
                _merge_into(existing, line)

    merged.sort(key=lambda ln: (ln.get("minute") is None, ln.get("minute") or 0.0))
    return merged


def _find_duplicate(merged: list[dict[str, Any]], line: dict[str, Any]) -> dict[str, Any] | None:
    """Return an already-merged line that represents the same event, or None.

    Same event := identical non-'none' `type` AND minutes within MINUTE_TOLERANCE.
    Ordinary play-by-play ('none') is never deduped — only stoppage signals are,
    since those are what feed detection and what providers redundantly report.
    """
    ltype = line.get("type")
    if not ltype or ltype == "none":
        return None
    lmin = line.get("minute")
    for cand in merged:
        if cand.get("type") != ltype:
            continue
        cmin = cand.get("minute")
        if lmin is None or cmin is None:
            # A same-type signal with a missing minute on either side can't be
            # placed precisely; fold it into the same-type event so the richer
            # (placed) line wins. Conservative: only matches same `type`.
            return cand
        if abs(float(cmin) - float(lmin)) <= MINUTE_TOLERANCE:
            return cand
    return None


def _merge_into(existing: dict[str, Any], line: dict[str, Any]) -> None:
    """Fold `line` into `existing` (same event): keep the richer evidence.

    - Prefer the longer text (more detail for downstream huddle/outcome heuristics).
    - Prefer a defined minute over a missing one.
    """
    new_text = line.get("text") or ""
    if len(new_text) > len(existing.get("text") or ""):
        existing["text"] = new_text
    if existing.get("minute") is None and line.get("minute") is not None:
        existing["minute"] = line["minute"]
