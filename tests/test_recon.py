"""Light tests for the offline momentum-reconstruction validation (synthetic; no ρ thresholds)."""

from __future__ import annotations

import math

from src.analysis import momentum_recon as mr


def test_parse_shots_maps_home_and_drops_null_xg():
    raw = {
        "general": {"homeTeam": {"id": 1}, "awayTeam": {"id": 2}},
        "content": {"shotmap": {"shots": [
            {"min": 10, "minAdded": 0, "expectedGoals": 0.3, "teamId": 1},
            {"min": 20, "minAdded": 2, "expectedGoals": 0.1, "teamId": 2},
            {"min": 30, "expectedGoals": None, "teamId": 1},   # dropped (no xG)
        ]}},
    }
    shots = mr.parse_shots(raw)
    assert len(shots) == 2
    assert shots[0] == {"m": 10.0, "xg": 0.3, "home": True}
    assert shots[1]["home"] is False and shots[1]["m"] == 22.0  # min + minAdded


def test_threat_proxy_orientation_and_length():
    shots = [{"m": 10.0, "xg": 0.5, "home": True}, {"m": 40.0, "xg": 0.5, "home": False}]
    px = mr.threat_proxy(shots, 60, tau=6.0)
    assert len(px) == 61
    assert px[12] > 0          # home shot -> positive
    assert px[42] < 0          # away shot -> negative
    assert px[5] == 0.0        # nothing before the first shot


def test_correlate_finite_and_self_is_one():
    px = mr.threat_proxy([{"m": 5.0, "xg": 0.4, "home": True},
                          {"m": 25.0, "xg": 0.6, "home": False}], 50)
    c = mr.correlate(px, px)
    assert math.isclose(c["pearson"], 1.0, abs_tol=1e-9)
    assert math.isfinite(c["spearman"])
