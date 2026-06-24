"""Stoppage detection — the treatment-definition step.

Consumes normalized inputs (match meta + SofaScore incidents + classified
commentary) and emits one match-level stoppage record per detected stoppage.
`src/features/momentum_features.py` later expands each into two team-perspective
rows and attaches momentum windows.

Detection sources by type:
  hydration  -> commentary (SofaScore has no hydration incident)
  var        -> SofaScore incidents (varDecision); commentary as fallback
  injury     -> commentary; split into injury_huddle / injury_no_huddle (heuristic)

This module is unit-tested offline against fixtures (CLAUDE.md requirement).
"""

from __future__ import annotations

from typing import Any

from src.paths import HYDRATION_NOMINAL_MINUTES

# Subs counted as "during the break" if they occur in this minute window
# relative to the stoppage clock minute. Subs typically come on after the break.
SUB_WINDOW = (-1.0, 2.0)

# Two hydration comments within this many minutes are the same break.
HYDRATION_CLUSTER_GAP = 3.0

# Heuristic proxy: an injury stoppage is tagged "huddle" iff a substitution was made
# during it. There is no per-stoppage dwell-time signal, so "with sub" is the observable
# stand-in for a coaching window — which makes the treatment label collinear with the
# sub_made_during_break control. The mechanism reading is interpretive, not identified;
# see the mechanism caveats in PROJECT_BRIEF.md.


def detect_stoppages(
    meta: dict[str, Any],
    incidents: list[dict[str, Any]],
    commentary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return match-level stoppage records (team-agnostic).

    Each record carries enough context for the features step and the regression:
    clock minute, type, pre-stoppage score/red-card state, and sub-at-break info.
    """
    match_id = meta.get("match_id")
    stoppages: list[dict[str, Any]] = []
    # ESPN tags every stoppage with a Start/End Delay carrying match-clock seconds; pair them once
    # so real_duration_seconds can be filled for ANY stoppage type (not just hydration).
    pairs = _delay_pairs(commentary)

    # --- hydration: cluster nearby hydration comments -----------------------
    for minute in _cluster_hydration(commentary):
        stoppages.append(
            _base_record(match_id, "hydration", minute, incidents,
                         duration=_duration_for(pairs, minute, hydration=True))
        )

    # --- VAR: incidents (SofaScore) AND commentary (FotMob+ESPN) ------------
    var_minutes = [i["minute"] for i in incidents if i["kind"] == "var" and i["minute"] is not None]
    for minute in var_minutes:
        rec = _base_record(match_id, "var", float(minute), incidents,
                           duration=_duration_for(pairs, float(minute)))
        # outcome class (goalAwarded / penaltyNotAwarded / ...) for split analysis
        rec["var_outcome"] = next(
            (i.get("detail") for i in incidents if i["kind"] == "var" and i["minute"] == minute),
            None,
        )
        stoppages.append(rec)
    # commentary-derived VARs (the only source when scraping FotMob), deduped vs incidents
    for minute in _cluster_commentary_type(commentary, "var"):
        if any(abs(minute - vm) <= 2 for vm in var_minutes):
            continue
        stoppages.append(_base_record(match_id, "var", minute, incidents,
                                      duration=_duration_for(pairs, minute)))

    # --- injuries: from commentary, classify huddle vs no_huddle ------------
    for minute in _cluster_commentary_type(commentary, "injury"):
        sub_during = _subs_in_window(incidents, minute)
        is_huddle = (sub_during["home"] + sub_during["away"]) > 0
        stype = "injury_huddle" if is_huddle else "injury_no_huddle"
        stoppages.append(_base_record(match_id, stype, minute, incidents,
                                      duration=_duration_for(pairs, minute)))

    # Stable ids in chronological order
    stoppages.sort(key=lambda s: s["clock_minute"])
    for idx, s in enumerate(stoppages):
        s["stoppage_id"] = f"{match_id}-{idx:02d}"
    return stoppages


# --- detection helpers ------------------------------------------------------


def _cluster_hydration(commentary: list[dict[str, Any]]) -> list[float]:
    """Representative minute per detected hydration break.

    Anchored on commentary (not the clock); spurious hits far from either nominal mark are
    dropped to reduce false positives from chatter.
    """
    hyd = [c for c in commentary if c.get("type") == "hydration" and c.get("minute") is not None]
    out = []
    for cl in _cluster(sorted(c["minute"] for c in hyd), HYDRATION_CLUSTER_GAP):
        m = sum(cl) / len(cl)
        if any(abs(m - nom) <= 12 for nom in HYDRATION_NOMINAL_MINUTES):
            out.append(round(m, 1))
    return out


# Sanity bounds (seconds) for a measured stoppage — discards mis-paired delays.
_MIN_BREAK_SEC, _MAX_BREAK_SEC = 5, 400


def _delay_pairs(commentary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pair each ESPN 'Start Delay' with the next 'End Delay' -> [{minute, duration}] in seconds.

    Two-pointer over match-clock `seconds`, so each resume is consumed once (handles back-to-back
    delays like a drinks break immediately followed by an injury delay). The match clock runs
    through stoppages, so end-minus-start is real elapsed time — not subject to commentary lag.
    """
    # A break's start is an explicit ESPN "Start Delay" OR any hydration-classified line carrying
    # seconds (some "drinks break" comments aren't tagged Start Delay but still timestamp the break).
    starts = sorted(
        (c for c in commentary
         if c.get("seconds") is not None and (c.get("delay") == "start" or c.get("type") == "hydration")),
        key=lambda c: c["seconds"])
    ends = sorted(c["seconds"] for c in commentary
                  if c.get("delay") == "end" and c.get("seconds") is not None)
    pairs: list[dict[str, Any]] = []
    j = 0
    for s in starts:
        while j < len(ends) and ends[j] <= s["seconds"]:
            j += 1
        if j >= len(ends):
            break
        dur = ends[j] - s["seconds"]
        j += 1
        if _MIN_BREAK_SEC <= dur <= _MAX_BREAK_SEC:
            pairs.append({"minute": s.get("minute"), "duration": round(dur), "type": s.get("type")})
    return pairs


def _duration_for(
    pairs: list[dict[str, Any]], minute: float, *, window: float = 3.0, hydration: bool = False
) -> float | None:
    """Duration (s) of the nearest delay pair to `minute`.

    A hydration break's Start Delay text ("drinks break") is itself hydration-classified, so we
    match it by type for precision; other stoppages take the nearest GENERIC delay (and never a
    hydration pair, so a VAR near a break can't steal the break's resume).
    """
    cand = [p for p in pairs if p.get("minute") is not None and abs(p["minute"] - minute) <= window]
    cand = [p for p in cand if (p.get("type") == "hydration") == hydration]
    if not cand:
        return None
    return min(cand, key=lambda p: abs(p["minute"] - minute))["duration"]


def _cluster_commentary_type(commentary: list[dict[str, Any]], label: str) -> list[float]:
    minutes = sorted(
        c["minute"] for c in commentary if c.get("type") == label and c.get("minute") is not None
    )
    return [round(sum(cl) / len(cl), 1) for cl in _cluster(minutes, 2.0)]


def _cluster(minutes: list[float], gap: float) -> list[list[float]]:
    """Group sorted minutes into clusters where consecutive gaps <= `gap`."""
    clusters: list[list[float]] = []
    for m in minutes:
        if clusters and m - clusters[-1][-1] <= gap:
            clusters[-1].append(m)
        else:
            clusters.append([m])
    return clusters


def _base_record(
    match_id: Any, stype: str, minute: float, incidents: list[dict[str, Any]],
    *, duration: float | None = None,
) -> dict[str, Any]:
    home_score, away_score = _score_at(incidents, minute)
    reds = _red_cards_before(incidents, minute)
    subs = _subs_in_window(incidents, minute)
    return {
        "match_id": match_id,
        "stoppage_type": stype,
        "clock_minute": float(minute),
        "real_duration_seconds": duration,  # ESPN start/end-delay second delta (hydration); else None
        "home_score_pre": home_score,
        "away_score_pre": away_score,
        "red_cards_home_pre": reds["home"],
        "red_cards_away_pre": reds["away"],
        "sub_made_during_break": (subs["home"] + subs["away"]) > 0,
        "subs_count_home": subs["home"],
        "subs_count_away": subs["away"],
        "var_outcome": None,
    }


def _score_at(incidents: list[dict[str, Any]], minute: float) -> tuple[int, int]:
    """Score (home, away) just before `minute`, from the last prior goal."""
    home, away = 0, 0
    for i in incidents:
        if i["kind"] == "goal" and i["minute"] is not None and i["minute"] <= minute:
            if i.get("home_score") is not None and i.get("away_score") is not None:
                home, away = int(i["home_score"]), int(i["away_score"])
            else:  # fall back to counting
                if i.get("is_home"):
                    home += 1
                else:
                    away += 1
    return home, away


def _red_cards_before(incidents: list[dict[str, Any]], minute: float) -> dict[str, int]:
    reds = {"home": 0, "away": 0}
    for i in incidents:
        if i["kind"] == "card" and i["minute"] is not None and i["minute"] <= minute:
            if (i.get("detail") or "").lower() in {"red", "yellowred"}:
                reds["home" if i.get("is_home") else "away"] += 1
    return reds


def _subs_in_window(incidents: list[dict[str, Any]], minute: float) -> dict[str, int]:
    lo, hi = minute + SUB_WINDOW[0], minute + SUB_WINDOW[1]
    subs = {"home": 0, "away": 0}
    for i in incidents:
        if i["kind"] == "substitution" and i["minute"] is not None and lo <= i["minute"] <= hi:
            subs["home" if i.get("is_home") else "away"] += 1
    return subs
