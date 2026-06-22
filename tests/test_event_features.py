"""Event-data lane tests: xT-flow momentum proxy + historical placebo.

Fetches ONE real 2022 men's WC match from StatsBomb open data (raw.githubusercontent
.com, no bot protection) and verifies the series + placebo table. All network use is
guarded so the suite SKIPS cleanly offline rather than failing.
"""

from __future__ import annotations

import math

import pytest

from src.features.momentum_features import COLUMNS, window_stats


def _pick_match_id() -> int:
    """First 2022 WC match id, or skip if the match list can't be fetched."""
    try:
        from src.scrape.statsbomb import fetch_matches

        matches = fetch_matches()
    except Exception as exc:  # noqa: BLE001 - network/offline guard
        pytest.skip(f"StatsBomb match list unavailable: {exc}")
    if not matches:
        pytest.skip("StatsBomb match list empty")
    return matches[0]["match_id"]


@pytest.fixture(scope="module")
def match_id() -> int:
    mid = _pick_match_id()
    # Ensure events are fetchable before any test runs; skip the whole module if not.
    try:
        from src.features.event_features import event_momentum_series

        event_momentum_series(mid)
    except Exception as exc:  # noqa: BLE001 - network/offline guard
        pytest.skip(f"StatsBomb events/xT-grid unavailable: {exc}")
    return mid


def _all_finite(series) -> bool:
    return all(math.isfinite(p["minute"]) and math.isfinite(p["value"]) for p in series)


def test_momentum_series_nonempty_and_finite(match_id):
    from src.features.event_features import event_momentum_series

    s = event_momentum_series(match_id)
    assert len(s) > 0
    assert _all_finite(s)
    # Shape is compatible with window_stats (keys + sortable minutes).
    assert all(set(p) == {"minute", "value"} for p in s)
    w = window_stats(s, 22.0)
    assert set(w) == {"pre_mean", "pre_slope", "post_mean", "post_slope", "delta"}


def test_field_tilt_in_range(match_id):
    from src.features.event_features import field_tilt_series

    s = field_tilt_series(match_id)
    assert len(s) > 0
    assert _all_finite(s)
    # Documented range: value = home_share - 0.5  ->  [-0.5, 0.5].
    assert all(-0.5 - 1e-9 <= p["value"] <= 0.5 + 1e-9 for p in s)


def test_shots_and_ppda(match_id):
    from src.features.event_features import ppda, shots_per_minute

    s = shots_per_minute(match_id)
    assert len(s) > 0
    assert _all_finite(s)
    p = ppda(match_id)
    assert set(p) == {"home", "away"}
    for v in p.values():
        assert v is None or (math.isfinite(v) and v >= 0)


def test_event_window_features_keys(match_id):
    from src.features.event_features import event_window_features

    feats = event_window_features(match_id, 67.0)
    expected = {
        "xt_pre", "xt_post", "field_tilt_pre", "field_tilt_post",
        "shots_pre", "shots_post", "ppda_pre", "ppda_post",
    }
    assert set(feats) == expected
    for v in feats.values():
        assert v is None or math.isfinite(v)


def test_historical_placebo_table_builds(match_id):
    from src.analysis.historical_placebo import (
        build_historical_placebo_table,
        summarize_placebo,
    )

    df = build_historical_placebo_table([match_id])
    assert df.columns == COLUMNS
    # Two team-perspective rows per placebo minute (22, 67) -> 4 rows.
    assert df.height == 4
    assert set(df["stoppage_type"].unique().to_list()) == {"placebo"}
    assert set(df["clock_minute"].unique().to_list()) == {22.0, 67.0}
    # Mirrored rows -> pooled delta is ~0 by construction.
    assert abs(sum(df["momentum_delta"].to_list())) < 1e-9

    summary = summarize_placebo(df, n_boot=200)
    assert set(summary) == {"mean_delta", "ci_lo", "ci_hi", "n", "n_matches"}
    assert summary["n_matches"] == 1
