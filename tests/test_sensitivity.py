"""Window-length sensitivity: leader-perspective delta sign + clustering (CI-safe, synthetic)."""

from __future__ import annotations

import polars as pl

from src.analysis import sensitivity as sv
from src.scrape import fotmob


def _patch_series(monkeypatch, series):
    monkeypatch.setattr(fotmob, "load_raw", lambda mid: {"_": 1})
    monkeypatch.setattr(fotmob, "parse_momentum", lambda raw: series)


def test_window_effect_home_on_top(monkeypatch):
    # home pressing pre-break (+20), cools after (+5) -> leader loses 15
    series = [{"minute": float(m), "value": 20.0} for m in range(25, 30)] + \
             [{"minute": float(m), "value": 5.0} for m in range(31, 36)]
    _patch_series(monkeypatch, series)
    df = pl.DataFrame({"match_id": ["M"], "clock_minute": [30.0], "stoppage_type": ["hydration"]})
    r = sv.window_effect(5.0, df=df)
    assert r["n"] == 1 and r["matches"] == 1
    assert abs(r["mean"] - (-15.0)) < 1e-6


def test_window_effect_away_on_top_uses_leader_perspective(monkeypatch):
    # away pressing pre-break (home momentum -20), eases after (-5) -> leader (away) loses 15 too
    series = [{"minute": float(m), "value": -20.0} for m in range(25, 30)] + \
             [{"minute": float(m), "value": -5.0} for m in range(31, 36)]
    _patch_series(monkeypatch, series)
    df = pl.DataFrame({"match_id": ["M"], "clock_minute": [30.0], "stoppage_type": ["hydration"]})
    r = sv.window_effect(5.0, df=df)
    assert abs(r["mean"] - (-15.0)) < 1e-6  # sign-flipped to the away leader's view
