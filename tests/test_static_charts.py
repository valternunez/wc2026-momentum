"""Tests for the static charts lane.

Builds stoppage-level rows from the synthetic fixture (via the real pipeline) and
asserts the static chart PNGs are written non-empty.

(The old methodology-appendix fragment lane was retired when the methodology moved to a
dedicated bilingual page — see tests/test_method.py.)
"""

from __future__ import annotations

import polars as pl
import pytest

from src.pipeline import assemble_rows
from src.viz.static_charts import save_static_charts

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def stoppage_df(match_inputs) -> pl.DataFrame:
    """Stoppage-level DataFrame from the synthetic fixture (offline)."""
    rows = assemble_rows(
        match_inputs["meta"],
        match_inputs["momentum"],
        match_inputs["incidents"],
        match_inputs["commentary"],
    )
    return pl.DataFrame(rows)


def _assert_valid_png(path: str) -> None:
    from pathlib import Path

    p = Path(path)
    assert p.exists(), f"missing {p}"
    data = p.read_bytes()
    assert len(data) > 1000, f"suspiciously small PNG: {p} ({len(data)} bytes)"
    assert data[:8] == PNG_MAGIC, f"not a PNG: {p}"


def test_save_static_charts_writes_pngs(stoppage_df, tmp_path):
    assert stoppage_df.height > 0
    paths = save_static_charts(stoppage_df, out_dir=tmp_path)
    assert len(paths) == 3
    names = {p.rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for p in paths}
    assert names == {"effect_by_type.png", "distribution.png", "momentum_timeline.png"}
    for p in paths:
        _assert_valid_png(p)


def test_save_static_charts_empty_df(tmp_path):
    """Empty input must not crash — placeholders are rendered instead."""
    empty = pl.DataFrame()
    paths = save_static_charts(empty, out_dir=tmp_path)
    assert len(paths) == 3
    for p in paths:
        _assert_valid_png(p)


def test_save_static_charts_default_out_dir(stoppage_df):
    """Default out_dir lands under SITE/figures (gitignored)."""
    from src.paths import SITE

    paths = save_static_charts(stoppage_df)
    for p in paths:
        assert str(SITE) in p
        _assert_valid_png(p)
