"""Tests for the social-artifact refresh guard (finding_signature + refresh_social).

The actual renders (og.png, story stills, story.mp4) need a browser + ffmpeg and are local-only, so
here we only test the signature/guard logic — never the rendering itself.
"""

from __future__ import annotations

import pytest

from src.paths import STOPPAGES_PARQUET
from src.report import build_site


def test_finding_signature_keys_and_stable():
    if not STOPPAGES_PARQUET.exists():
        pytest.skip("no processed data committed")
    sig = build_site.finding_signature()
    if not sig:
        pytest.skip("empty processed data")
    # the headline numbers the social artifacts depend on
    for k in ("hero", "p26", "n_matches", "gap", "gap_lo", "gap_hi", "gap_excl0"):
        assert k in sig, f"signature missing {k}"
    assert isinstance(sig["n_matches"], int)
    assert sig == build_site.finding_signature()   # deterministic across calls


def test_refresh_social_noop_when_state_matches(monkeypatch, tmp_path):
    """When render_state.json already matches the current signature, refresh_social must NOT call any
    renderer (the whole point of the change-guard — no daily binary churn)."""
    from src.viz import social

    sig = {"hero": 24, "p26": 19, "n_matches": 48, "gap": 3,
           "gap_lo": -3, "gap_hi": 9, "gap_excl0": False, "snap": "2026-06-24"}
    state = tmp_path / "render_state.json"
    import json

    state.write_text(json.dumps(sig, indent=2, sort_keys=True), encoding="utf-8")

    monkeypatch.setattr(social, "RENDER_STATE", state)
    # refresh_social imports finding_signature from build_site at call time → patch it there
    monkeypatch.setattr(build_site, "finding_signature", lambda: sig)

    called = []
    monkeypatch.setattr(social, "build_share_card", lambda *a, **k: called.append("og"))
    monkeypatch.setattr(social, "build_story_cards", lambda *a, **k: called.append("cards"))
    monkeypatch.setattr(social, "build_story_video", lambda *a, **k: called.append("video"))

    result = social.refresh_social()
    assert result == "up-to-date"
    assert called == [], "renderers must not run when the signature is unchanged"


def test_refresh_social_renders_when_changed(monkeypatch, tmp_path):
    """When the signature differs, refresh_social runs the renderers and advances render_state.json."""
    from src.viz import social

    state = tmp_path / "render_state.json"   # absent → forces a render
    new_sig = {"hero": 25, "p26": 18, "n_matches": 52, "gap": 4,
               "gap_lo": -2, "gap_hi": 10, "gap_excl0": False, "snap": "2026-06-25"}

    monkeypatch.setattr(social, "RENDER_STATE", state)
    monkeypatch.setattr(build_site, "finding_signature", lambda: new_sig)

    called = []
    monkeypatch.setattr(social, "build_share_card", lambda *a, **k: called.append("og"))
    monkeypatch.setattr(social, "build_story_cards", lambda *a, **k: called.append("cards"))
    monkeypatch.setattr(social, "build_story_video", lambda *a, **k: called.append("video"))

    result = social.refresh_social()
    assert result == "rendered"
    assert set(called) == {"og", "cards", "video"}
    assert state.exists()
    import json

    assert json.loads(state.read_text(encoding="utf-8")) == new_sig
