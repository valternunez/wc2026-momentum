"""Tests for the signed-off causal regression spec.

Covers: (1) the unit-of-analysis fix (one row per stoppage, not both mirrors),
(2) the momentum-killer interaction recovers a planted effect with the right sign,
(3) the machinery fits the real historical-placebo data and finds no hydration term.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from src.analysis.regression import (
    momentum_killer_estimate,
    run_twfe,
    to_regression_frame,
)

_TEAMS = [f"T{i}" for i in range(8)]
_TYPES = ["hydration", "var", "injury_huddle", "injury_no_huddle"]


def _row(match_id, sid, stype, is_home, team, opp, pre, delta, score):
    return {
        "match_id": match_id,
        "stoppage_id": sid,
        "stoppage_type": stype,
        "var_outcome": None,
        "is_home": is_home,
        "team": team,
        "opponent": opp,
        "momentum_pre_5min_mean": pre,
        "momentum_delta": delta,
        "score_diff_pre": score,
    }


def _synthetic(n_matches=20, *, beta=1.0, noise=2.0, seed=0) -> pl.DataFrame:
    """Stoppage table (both perspectives) with a planted hydration momentum-killer.

    For hydration, momentum_delta = -beta * pre_momentum (+ noise): when the home
    team was on top (pre>0) it loses momentum. Other types have no such slope.
    """
    rng = np.random.default_rng(seed)
    rows = []
    sid = 0
    for m in range(n_matches):
        home, away = _TEAMS[m % 8], _TEAMS[(m + 3) % 8]
        for stype in _TYPES:
            pre = float(rng.normal(0, 10))
            base = float(rng.normal(0, noise))
            delta = (-beta * pre + base) if stype == "hydration" else (base)
            score = int(rng.integers(-1, 2))
            sid += 1
            rows.append(_row(m, f"s{sid}", stype, True, home, away, pre, delta, score))
            rows.append(_row(m, f"s{sid}", stype, False, away, home, -pre, -delta, -score))
    return pl.DataFrame(rows)


def test_to_regression_frame_one_row_per_stoppage():
    df = _synthetic(n_matches=20)
    pdf = to_regression_frame(df)
    # 20 matches x 4 stoppages = 80 stoppages; both-perspective table has 160 rows
    assert df.height == 160
    assert len(pdf) == 80
    assert pdf["is_home"].all()


def test_recovers_planted_momentum_killer():
    df = _synthetic(n_matches=20, beta=1.0, noise=2.0, seed=1)
    result = run_twfe(df, with_interaction=True, control_pre_momentum=True)
    est = momentum_killer_estimate(result)
    assert est, "hydration interaction term should exist (VAR is the reference)"
    assert est["coef"] < 0, "planted killer effect is negative (momentum shifts off the top team)"
    assert est["pvalue"] < 0.05


def test_no_interaction_when_disabled():
    df = _synthetic(n_matches=20, seed=2)
    result = run_twfe(df, with_interaction=False, control_pre_momentum=True)
    assert momentum_killer_estimate(result) == {}


def test_small_sample_guard():
    df = _synthetic(n_matches=3)  # below MIN_MATCHES
    with pytest.raises(ValueError, match="Not enough data"):
        run_twfe(df)


def test_fits_real_historical_placebo_with_no_hydration_term():
    parquet = Path("data/processed/historical_placebo.parquet")
    if not parquet.exists():
        pytest.skip("run `python -m src.pipeline --historical-placebo` first")
    df = pl.read_parquet(parquet)
    result = run_twfe(df, with_interaction=True)
    # placebo data has a single stoppage_type -> no hydration interaction exists
    assert momentum_killer_estimate(result) == {}
    # the RTM control (pre-momentum slope) should be present and finite
    assert "momentum_pre_5min_mean" in result.params.index
    assert np.isfinite(result.params["momentum_pre_5min_mean"])
