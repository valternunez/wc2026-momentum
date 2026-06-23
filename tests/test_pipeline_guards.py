"""Phase-2 guardrails: the row-count regression guard must block garbage overwrites."""

from __future__ import annotations

import pytest

from src.pipeline import _guard_rowcount


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
