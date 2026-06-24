"""Phase-2 guardrails: the row-count regression guard must block garbage overwrites,
and the competition gate must keep non-WC2026 matches out of the dataset."""

from __future__ import annotations

import pytest

from src import pipeline
from src.pipeline import _guard_rowcount, _is_wc2026


def test_guard_rowcount_allows_normal_and_growth():
    _guard_rowcount(0, 0, force=False)        # no prior parquet -> always ok
    _guard_rowcount(100, 100, force=False)    # unchanged
    _guard_rowcount(100, 140, force=False)    # growth (tournament progressing)
    _guard_rowcount(100, 60, force=False)     # mild dip, >50% kept


def test_guard_rowcount_blocks_big_drop_unless_forced():
    with pytest.raises(RuntimeError):
        _guard_rowcount(100, 40, force=False)  # >50% drop -> refuse
    with pytest.raises(RuntimeError):
        _guard_rowcount(100, 0, force=False)   # empty -> refuse
    _guard_rowcount(100, 0, force=True)        # ...unless explicitly forced


def test_wc2026_gate_admits_only_parent_league_77(monkeypatch):
    # WC2026 group/knockout leagues sit under FotMob parentLeagueId 77; qualifiers (10195/10199),
    # Euro (50) and Copa (44) must be rejected even if their raw lands in RAW_FOTMOB.
    raws = {
        "wc": {"general": {"parentLeagueId": 77, "leagueName": "World Cup Grp. A"}},
        "uefa_qual": {"general": {"parentLeagueId": 10195, "leagueName": "World Cup Qualification UEFA"}},
        "euro": {"general": {"parentLeagueId": 50, "leagueName": "EURO"}},
        "missing": {},  # unreadable/absent raw
    }
    monkeypatch.setattr(pipeline.fotmob, "load_raw", lambda mid: raws.get(mid, {}))
    assert _is_wc2026("wc") is True
    assert _is_wc2026("uefa_qual") is False
    assert _is_wc2026("euro") is False
    assert _is_wc2026("missing") is False
