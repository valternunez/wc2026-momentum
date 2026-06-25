"""Tests for the bilingual ~15s kinetic reel pages (reel.html + reel.es.html).

The MP4 render needs a browser + ffmpeg and is local-only (like og.png); here we only test that the
pages build, resolve every token, carry the data numbers, and embed the timeline.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.paths import SITE
from src.report import build_site
from src.report.i18n import LANGS, STRINGS
from src.report.reel_copy import TEMPLATE as REEL_TEMPLATE


def _build_pages() -> tuple[str, str] | None:
    index = Path(build_site.build())
    if "No data yet" in index.read_text(encoding="utf-8"):
        return None
    en = (SITE / "reel.html").read_text(encoding="utf-8")
    es = (SITE / "reel.es.html").read_text(encoding="utf-8")
    return en, es


def test_reel_template_has_no_backslash_doublequote():
    assert '\\"' not in REEL_TEMPLATE


def test_reel_pages_built_and_resolved():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    en, es = pages
    for html in (en, es):
        assert "{{" not in html              # every token substituted (also guarded in build())
        assert "<!DOCTYPE html>" in html
        assert html.count('class="scene"') == 5            # hook · proof · twist · verdict · cta
        assert "setTimeout" in html and "data-scene" in html  # the kinetic timeline is embedded
        assert "95% CI" in html                            # verdict carries the interval
        # the myth-buster pair (break drop vs no-break control) both appear
        assert html.count("&#8722;") >= 3                  # at least the -hero (x2) + -p26 numbers
    # honest verdict clause, CI-templated, in each language
    assert ("not proven" in en) or ("really bites" in en)
    assert ("sin probar" in es) or ("sí pega" in es)


def test_reel_strings_bilingual_parity():
    keys = {k for k in STRINGS["en"] if k.startswith("REEL_")}
    assert keys, "no REEL_ keys found"
    for lang in LANGS:
        missing = keys - set(STRINGS[lang])
        assert not missing, f"{lang} is missing reel keys: {sorted(missing)}"


def test_story_links_to_reel_download():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    story = (SITE / "story.html").read_text(encoding="utf-8")
    story_es = (SITE / "story.es.html").read_text(encoding="utf-8")
    assert 'href="reel.mp4"' in story
    assert 'href="reel.es.mp4"' in story_es
