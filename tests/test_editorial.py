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
    # §05 break-vs-no-break comparison chart (incl. the within-2026 placebo) + honest caption
    assert "Club World Cup 2025" in html and "World Cup 2022" in html
    assert "same 2026 matches" in html and "Same statistic, same scale" in html
    assert "Did they even need them" in html and "WBGT" in html
    # match grid grouped by stage, in collapsible <details> sections
    assert "Group A" in html and "grouped by stage" in html
    assert '<details class="grp"' in html and '<summary class="grp-h"' in html
    assert "max-width:700px" in html  # mobile default-collapse JS present
    # modal share toolbar + team-named legend + themed-export data
    assert 'id="mb-share"' in html and 'id="mb-leg-home"' in html
    assert 'data-group="palette"' in html and 'data-group="mode"' in html
    assert '"ts"' in html and '"colors"' in html  # date + kit colours embedded for the modal
    # §03 "the extremes" (matches, not teams) + honest note
    assert "The extremes" in html and "Biggest swings" in html and "Quietest breaks" in html
    assert "matches and not teams" in html and "break-prone" in html
    # match date on grid cards (DD/MM/YYYY)
    import re
    assert re.search(r"\d{2}/\d{2}/\d{4}", html)
    # goal markers: data embedded + legend entry (clean disc marker, no emoji)
    assert '"goals"' in html and ">GOAL</span>" in html
    assert "⚽" not in html  # emoji replaced by the editorial disc marker
    # VAR marker distinct from hydration: violet + dotted, old green gone
    assert "dotted #7A5CC0" in html and "#2E8B57" not in html
    # data-freshness banner wired (hidden by default; JS reveals if snapshot is stale)
    assert 'id="freshness"' in html and 'var iso=' in html
    # modal a11y: focus trap, restore-focus, and SVG screen-reader labelling
    assert "trapTab" in html and "lastFocus" in html
    assert "aria-label" in html and "el('title'" in html  # svg/goal titles for screen readers


def test_parse_goals():
    raw = {"content": {"matchFacts": {"events": {"events": [
        {"type": "Goal", "time": 9, "isHome": True, "nameStr": "A", "newScore": [1, 0], "goalDescriptionKey": ""},
        {"type": "Goal", "time": 50, "isHome": False, "nameStr": "B", "newScore": [1, 1], "goalDescriptionKey": "penalty"},
        {"type": "Goal", "time": 60, "isHome": True, "nameStr": "C", "newScore": [2, 1], "ownGoal": True},
        {"type": "MissedPenalty", "time": 70, "isHome": False, "nameStr": "D"},
        {"type": "Goal", "time": 121, "isHome": True, "nameStr": "E", "isPenaltyShootoutEvent": True, "newScore": [3, 1]},
        {"type": "Card", "time": 30, "isHome": True},
    ]}}}}
    g = fotmob.parse_goals(raw)
    assert [x["m"] for x in g] == [9, 50, 60, 70]  # shootout + card excluded, sorted by minute
    assert g[0]["sc"] == "1-0" and g[0]["k"] == ""
    assert g[1]["k"] == "pen" and g[1]["h"] == 0
    assert g[2]["k"] == "og"
    assert g[3]["k"] == "miss" and g[3]["sc"] == ""


def test_fmt_date_helpers_distinct():
    # regression guard: the ISO and epoch formatters must not shadow each other
    from src.report.build_site import _fmt_date_epoch, _fmt_date_iso

    iso = _fmt_date_iso("2026-06-22")
    assert "2026" in iso and "22" in iso          # "22 Jun 2026"-style
    assert _fmt_date_iso(None)                      # falls back to today (non-empty)
    assert _fmt_date_epoch(1781204400) == "11/06/2026"
    assert _fmt_date_epoch("2026-06-22") == ""      # epoch fn rejects ISO strings, doesn't crash
    assert _fmt_date_epoch(None) == ""


def test_stage_meta():
    from src.report.build_site import _stage_meta

    assert _stage_meta("World Cup Grp. J", "2")[0] == "Group J"
    assert _stage_meta("World Cup Final Stage", "1/8")[0] == "Round of 16"
    assert _stage_meta("World Cup Final Stage", "1/4")[0] == "Quarter-finals"
    assert _stage_meta("World Cup", "final")[0] == "Final"
    # groups sort before knockouts
    assert _stage_meta("World Cup Grp. A", "1")[1] < _stage_meta("World Cup", "final")[1]
