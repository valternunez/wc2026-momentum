"""Event-derived momentum features from StatsBomb open data (2022 men's WC).

These fill the event columns of the stoppage-level schema (xt/field_tilt/shots/ppda
pre/post) and provide an xT-flow momentum PROXY used as the outcome series for the
historical placebo (there is NO SofaScore momentum for 2022 — see
`src/analysis/historical_placebo.py`).

Pipeline (events -> SPADL -> xT), documented choices
----------------------------------------------------
* We read raw events from `src/scrape/statsbomb.fetch_events` (cached, idempotent)
  and flatten them with the *same* `_flatten_id` the socceraction StatsBombLoader
  uses, so we do NOT need the optional `statsbombpy` dependency (the "remote" getter
  requires it; it is not installed). This is the simplest reliable path.
* SPADL actions via `socceraction.spadl.statsbomb.convert_to_actions`, names added,
  oriented left-to-right per team with `play_left_to_right`.
* xT: we LOAD Karun Singh's pretrained 12x8 grid from the socceraction-documented URL
  (`https://karun.in/blog/data/open_xt_12x8_v1.json`) via `xthreat.load_model`. We do
  not fit our own grid — the pretrained surface is deterministic, reproducible and
  avoids needing many matches to fit. `model.rate` only values *move* actions; all
  other actions (shots, fouls, defensive) get NaN, which we treat as 0 contribution.

Conventions
-----------
* Series shape: `[{"minute": float, "value": float}]`, value HOME-POSITIVE, sorted by
  minute — directly compatible with `momentum_features.window_stats`.
* Minute of an action = `(period_id - 1) * 45 + time_seconds / 60`. We bucket actions
  into integer-minute bins and emit the series at bin centers (`bin + 0.5`).

Field-tilt sign convention
--------------------------
`value = home_final_third_touch_share - 0.5`, range [-0.5, 0.5]. Positive => home is
camped in the opponent's final third (home-positive, consistent with momentum). The
raw per-team share is in [0, 1]; the centered series is in [-0.5, 0.5].

PPDA definition
---------------
Passes Allowed Per Defensive Action: for a pressing team T,
`opponent_passes_in_T's_attacking_60% / T's_defensive_actions_in_that_zone`, where
defensive actions = {tackle, interception, foul, challenge/take_on-against}. Lower
PPDA = more intense pressing. Computed in the attacking 60% of the pitch (x > 0.4*105
in left-to-right coordinates). We report PPDA per team over a window; this is a level
(not a home-positive flow), so the convenience features return raw per-team values.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

import socceraction.data.statsbomb.loader as _sbloader
import socceraction.spadl as spadl
import socceraction.xthreat as xthreat

from src.scrape.statsbomb import fetch_events, fetch_matches

# socceraction-documented pretrained xT grid (Karun Singh, 12x8).
XT_GRID_URL = "https://karun.in/blog/data/open_xt_12x8_v1.json"

FIELD_LENGTH = spadl.config.field_length  # 105.0
FIELD_WIDTH = spadl.config.field_width    # 68.0
FINAL_THIRD_X = FIELD_LENGTH * 2.0 / 3.0  # 70.0
PRESS_ZONE_X = FIELD_LENGTH * 0.4         # 42.0 -> attacking 60%

# Defensive actions counted for PPDA.
_DEF_ACTIONS = {"tackle", "interception", "foul", "challenge"}
_SHOT_ACTIONS = {"shot", "shot_penalty", "shot_freekick"}


# --------------------------------------------------------------------------- #
# Match metadata + SPADL/xT core (cached per match)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=8)
def _home_team_id(match_id: int) -> int:
    for m in fetch_matches():
        if m["match_id"] == match_id:
            return m["home_team"]["home_team_id"]
    raise ValueError(f"match_id {match_id} not in 2022 WC match list")


def _events_dataframe(match_id: int) -> pd.DataFrame:
    """Raw cached events -> loader-shaped DataFrame (no statsbombpy needed)."""
    obj = fetch_events(match_id)
    df = pd.DataFrame(_sbloader._flatten_id(e) for e in obj)
    df.rename(columns={"id": "event_id", "period": "period_id"}, inplace=True)
    df["game_id"] = match_id
    df["timestamp"] = pd.to_timedelta(df["timestamp"])
    if "related_events" not in df:
        df["related_events"] = [[] for _ in range(len(df))]
    df["related_events"] = df["related_events"].apply(lambda d: d if isinstance(d, list) else [])
    for col in ("under_pressure", "counterpress"):
        if col not in df:
            df[col] = False
        df[col] = df[col].astype(object).where(df[col].notna(), False).astype(bool)
    return df


@lru_cache(maxsize=8)
def _actions(match_id: int) -> pd.DataFrame:
    """SPADL actions (left-to-right) with an `xt` value and a `minute` column."""
    home = _home_team_id(match_id)
    events = _events_dataframe(match_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        actions = spadl.statsbomb.convert_to_actions(events, home)
    actions = spadl.add_names(actions)
    ltr = spadl.play_left_to_right(actions, home)
    model = _xt_model()
    xt = np.asarray(model.rate(ltr), dtype=float)
    xt[~np.isfinite(xt)] = 0.0
    out = ltr.copy()
    out["xt"] = xt
    out["minute"] = (out["period_id"] - 1) * 45.0 + out["time_seconds"] / 60.0
    out["is_home"] = out["team_id"] == home
    return out


@lru_cache(maxsize=1)
def _xt_model() -> "xthreat.ExpectedThreat":
    return xthreat.load_model(XT_GRID_URL)


def _bins(actions: pd.DataFrame) -> np.ndarray:
    """Integer-minute bins present in the match (0..max)."""
    last = int(np.floor(actions["minute"].max())) if len(actions) else 0
    return np.arange(0, last + 1)


def _series_from_bins(bins: np.ndarray, values: np.ndarray, smooth: int = 3) -> list[dict]:
    """Emit a [{minute, value}] series at bin centers, optionally smoothed."""
    if smooth and smooth > 1 and len(values):
        kernel = np.ones(smooth) / smooth
        values = np.convolve(values, kernel, mode="same")
    return [
        {"minute": float(b) + 0.5, "value": float(v)}
        for b, v in zip(bins, values)
    ]


# --------------------------------------------------------------------------- #
# Public series builders
# --------------------------------------------------------------------------- #
def event_momentum_series(match_id: int, smooth: int = 3) -> list[dict]:
    """Per-minute, home-positive xT-flow momentum proxy for one match.

    Sums each action's xT, signed +home / -away, into integer-minute bins and
    applies a centered rolling mean (default window 3). Output is sorted by minute
    and shaped for `momentum_features.window_stats`.
    """
    a = _actions(match_id)
    bins = _bins(a)
    signed = a["xt"] * np.where(a["is_home"], 1.0, -1.0)
    binned = np.floor(a["minute"]).astype(int).clip(0, bins[-1] if len(bins) else 0)
    agg = np.zeros(len(bins))
    for b, v in zip(binned.to_numpy(), signed.to_numpy()):
        agg[b] += v
    return _series_from_bins(bins, agg, smooth=smooth)


def field_tilt_series(match_id: int, smooth: int = 3) -> list[dict]:
    """Per-minute home-positive final-third touch tilt.

    value = home_final_third_touch_share - 0.5, in [-0.5, 0.5]. A "touch" is any
    action whose start location is in that team's attacking final third (x > 70 in
    its own left-to-right frame). Minutes with no final-third touches yield value 0.
    """
    a = _actions(match_id)
    bins = _bins(a)
    in_ft = a["start_x"] > FINAL_THIRD_X
    home_ft = (in_ft & a["is_home"]).to_numpy()
    away_ft = (in_ft & ~a["is_home"]).to_numpy()
    binned = np.floor(a["minute"]).astype(int).clip(0, bins[-1] if len(bins) else 0).to_numpy()
    h = np.zeros(len(bins))
    w = np.zeros(len(bins))
    for b, hf, wf in zip(binned, home_ft, away_ft):
        h[b] += hf
        w[b] += wf
    total = h + w
    share = np.divide(h, total, out=np.full(len(bins), 0.5), where=total > 0)
    return _series_from_bins(bins, share - 0.5, smooth=smooth)


def shots_per_minute(match_id: int, smooth: int = 0) -> list[dict]:
    """Per-minute home-positive shot count (home shots - away shots per minute)."""
    a = _actions(match_id)
    bins = _bins(a)
    is_shot = a["type_name"].isin(_SHOT_ACTIONS)
    signed = np.where(a["is_home"], 1.0, -1.0) * is_shot.to_numpy()
    binned = np.floor(a["minute"]).astype(int).clip(0, bins[-1] if len(bins) else 0).to_numpy()
    agg = np.zeros(len(bins))
    for b, v in zip(binned, signed):
        agg[b] += v
    return _series_from_bins(bins, agg, smooth=smooth)


def ppda(match_id: int, *, lo: float | None = None, hi: float | None = None) -> dict[str, float | None]:
    """PPDA per team over a minute interval [lo, hi) (whole match if None).

    Returns {"home": float|None, "away": float|None}. Lower = more pressing.
    None when a team has zero defensive actions in the zone (PPDA undefined).
    """
    a = _actions(match_id)
    if lo is not None:
        a = a[a["minute"] >= lo]
    if hi is not None:
        a = a[a["minute"] < hi]
    out: dict[str, float | None] = {}
    for side, is_home in (("home", True), ("away", False)):
        presser = a[a["is_home"] == is_home]
        opp = a[a["is_home"] != is_home]
        # Pressing team's defensive actions in the attacking 60% (x > PRESS_ZONE_X).
        def_actions = presser[
            presser["type_name"].isin(_DEF_ACTIONS) & (presser["start_x"] > PRESS_ZONE_X)
        ].shape[0]
        # Opponent passes in that same zone (opponent's own defensive 60%, i.e.
        # x < FIELD_LENGTH - PRESS_ZONE_X in the opponent's own L->R frame).
        opp_passes = opp[
            opp["type_name"].isin({"pass", "cross"}) & (opp["start_x"] < FIELD_LENGTH - PRESS_ZONE_X)
        ].shape[0]
        out[side] = (opp_passes / def_actions) if def_actions > 0 else None
    return out


# --------------------------------------------------------------------------- #
# Convenience: window features around a stoppage center (fills schema columns)
# --------------------------------------------------------------------------- #
def _window_mean(series: list[dict], center: float, window: float, *, side: str) -> float | None:
    """Mean of a home-positive series over the pre/post window."""
    if side == "pre":
        pts = [p["value"] for p in series if center - window <= p["minute"] < center]
    else:
        pts = [p["value"] for p in series if center < p["minute"] <= center + window]
    return float(np.mean(pts)) if pts else None


def event_window_features(match_id: int, center: float, window: float = 5.0) -> dict:
    """Pre/post event features around a stoppage `center` minute (home-positive).

    Returns keys matching the schema columns the lead must fill:
        xt_pre, xt_post, field_tilt_pre, field_tilt_post,
        shots_pre, shots_post, ppda_pre, ppda_post
    xt/field_tilt/shots are HOME-POSITIVE means of the per-minute series; ppda_* are
    (home_ppda - away_ppda) over the window so the value is also home-oriented
    (negative => home pressing harder than the away side). All can be None when the
    window has no data.
    """
    xt = event_momentum_series(match_id)
    ft = field_tilt_series(match_id)
    sh = shots_per_minute(match_id)

    def _ppda_diff(lo: float, hi: float) -> float | None:
        p = ppda(match_id, lo=lo, hi=hi)
        if p["home"] is None or p["away"] is None:
            return None
        return p["home"] - p["away"]

    return {
        "xt_pre": _window_mean(xt, center, window, side="pre"),
        "xt_post": _window_mean(xt, center, window, side="post"),
        "field_tilt_pre": _window_mean(ft, center, window, side="pre"),
        "field_tilt_post": _window_mean(ft, center, window, side="post"),
        "shots_pre": _window_mean(sh, center, window, side="pre"),
        "shots_post": _window_mean(sh, center, window, side="post"),
        "ppda_pre": _ppda_diff(center - window, center),
        "ppda_post": _ppda_diff(center, center + window),
    }
