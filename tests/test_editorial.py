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


def test_match_panels_skip_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(fotmob, "load_raw", lambda mid: FIX)
    assert per_match.build_match_panels(tmp_path, match_ids=["3370572"]) == ["3370572"]
    # second run skips the already-rendered panel (no churn)
    assert per_match.build_match_panels(tmp_path, match_ids=["3370572"]) == []
    # force re-renders
    assert per_match.build_match_panels(tmp_path, match_ids=["3370572"], force=True) == ["3370572"]


def test_build_editorial_page():
    html = Path(build_site.build()).read_text(encoding="utf-8")
    if "No data yet" in html:
        pytest.skip("no processed data committed")
    assert "Do hydration breaks really kill momentum" in html
    assert "{{" not in html  # every token substituted
    assert "SofaScore" not in html and "FotMob" in html  # accuracy: FotMob, not SofaScore
    assert "mb-card" in html  # match grid present
    assert "Hydration break" in html  # money chart / mechanism labels
    # interactive modal wiring
    assert 'id="mb-modal"' in html and 'id="mb-data"' in html
    assert "data-mid=" in html        # clickable cards
    assert '"series"' in html and '"explain"' in html  # embedded momentum + per-match note
    # social meta + favicon
    assert 'property="og:image"' in html and 'name="twitter:card"' in html
    assert 'rel="apple-touch-icon"' in html and 'rel="icon"' in html
    # momentum explainer (we read it, not compute it)
    assert "we don't compute it" in html or "we don't compute our own" in html
    # §05 two same-units placebos + §06 heat note
    assert "2025 Club World Cup" in html and "2022 World Cup" in html
    assert "Did they even need them" in html and "WBGT" in html
    # match grid grouped by stage
    assert "Group A" in html and "grouped by stage" in html
    # modal share toolbar + team-named legend + themed-export data
    assert 'id="mb-share"' in html and 'id="mb-leg-home"' in html
    assert 'data-group="palette"' in html and 'data-group="mode"' in html
    assert '"ts"' in html and '"colors"' in html  # date + kit colours embedded for the modal


def test_stage_meta():
    from src.report.build_site import _stage_meta

    assert _stage_meta("World Cup Grp. J", "2")[0] == "Group J"
    assert _stage_meta("World Cup Final Stage", "1/8")[0] == "Round of 16"
    assert _stage_meta("World Cup Final Stage", "1/4")[0] == "Quarter-finals"
    assert _stage_meta("World Cup", "final")[0] == "Final"
    # groups sort before knockouts
    assert _stage_meta("World Cup Grp. A", "1")[1] < _stage_meta("World Cup", "final")[1]
