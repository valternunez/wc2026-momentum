"""Test the per-match momentum grid renderer (offline, against the FotMob fixture)."""

from __future__ import annotations

import json
from pathlib import Path

from src.scrape import fotmob
from src.viz import per_match

FIX = json.loads(
    (Path(__file__).parent / "fixtures" / "fotmob_match" / "matchDetails.json").read_text(encoding="utf-8")
)


def test_empty_returns_none(tmp_path):
    # no matches -> nothing to draw, no crash (e.g. CI with no FotMob raw)
    assert per_match.build_per_match_grid(tmp_path / "g.png", match_ids=[]) is None


def test_renders_png(tmp_path, monkeypatch):
    monkeypatch.setattr(fotmob, "load_raw", lambda mid: FIX)
    out = per_match.build_per_match_grid(tmp_path / "g.png", match_ids=["3370572"])
    assert out is not None
    p = Path(out)
    assert p.exists() and p.stat().st_size > 1000  # a real PNG was written
