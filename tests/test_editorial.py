"""Tests for the editorial report build + per-match panels."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.report import build_site
from src.scrape import fotmob
from src.viz import per_match

FIX = json.loads(
    (Path(__file__).parent / "fixtures" / "fotmob_match" / "matchDetails.json").read_text(encoding="utf-8")
)


def test_match_panels_render(tmp_path, monkeypatch):
    monkeypatch.setattr(fotmob, "load_raw", lambda mid: FIX)
    ids = per_match.build_match_panels(tmp_path, match_ids=["3370572"])
    assert ids == ["3370572"]
    assert (tmp_path / "3370572.png").stat().st_size > 1000  # a real PNG


def test_match_panels_empty(tmp_path):
    assert per_match.build_match_panels(tmp_path, match_ids=[]) == []


def test_build_editorial_page():
    html = Path(build_site.build()).read_text(encoding="utf-8")
    if "No data yet" in html:
        pytest.skip("no processed data committed")
    assert "Do water breaks really kill momentum" in html
    assert "{{" not in html  # every token substituted
    assert "SofaScore" not in html and "FotMob" in html  # accuracy: FotMob, not SofaScore
    assert "mb-card" in html  # match grid present
    assert "Hydration break" in html  # money chart / mechanism labels
