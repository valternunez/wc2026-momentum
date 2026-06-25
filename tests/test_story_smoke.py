"""Tests for the bilingual 9:16 story-mode pages (story.html + story.es.html) and the share bar."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.paths import SITE
from src.report import build_site
from src.report.i18n import LANGS, STRINGS
from src.report.story_copy import TEMPLATE as STORY_TEMPLATE


def _build_pages() -> tuple[str, str] | None:
    """Build the site; return (en, es) story HTML or None if no data is committed."""
    index = Path(build_site.build())
    if "No data yet" in index.read_text(encoding="utf-8"):
        return None
    en = (SITE / "story.html").read_text(encoding="utf-8")
    es = (SITE / "story.es.html").read_text(encoding="utf-8")
    return en, es


def test_story_template_has_no_backslash_doublequote():
    """editorial/method/story TEMPLATEs are NON-raw strings: a literal \\" would collapse and break
    the inline JS. Single-quoted attrs/JS only."""
    assert '\\"' not in STORY_TEMPLATE


def test_story_pages_built_and_resolved():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    en, es = pages
    for html in (en, es):
        assert "{{" not in html              # every token substituted (also guarded in build())
        assert "<!DOCTYPE html>" in html
        assert html.count('class="slide"') == 6        # six narrative slides
        assert 'id="frame"' in html
        assert "URLSearchParams" in html               # nav/still/autoplay script embedded
        assert "autoplay" in html and "body.classList.add('autoplay')" in html  # video-capture mode
        assert 'href="story.mp4"' in html or 'href="story.es.mp4"' in html      # download-video link
    # the headline numbers reach the slides (they trace to the committed parquet)
    assert "data-num=" in en
    # verdict slide carries the CI bounds + the data-driven gap clause (honest verdict)
    assert "95% CI" in en
    assert ("includes zero" in en) or ("sits clear of zero" in en)
    assert ("incluye el cero" in es) or ("queda lejos del cero" in es)


def test_story_share_and_nav_links():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    en, es = pages
    # share bar present with all three intent targets + copy + native hooks
    for html in (en, es):
        assert 'class="sharebar"' in html
        assert "wa.me" in html and "twitter.com/intent/tweet" in html and "t.me/share/url" in html
        assert "data-copy=" in html and "data-native" in html
    # back-link to the analysis + cross-language story sibling
    assert 'href="index.html"' in en and 'href="story.es.html"' in en
    assert 'href="index.es.html"' in es and 'href="story.html"' in es


def test_main_page_story_share_entry_points():
    """The main-page Story + share entry points follow the STORY_SHARE_ENABLED feature flag — present
    when enabled, fully absent when temporarily hidden (the pages/code stay built either way)."""
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    index = (SITE / "index.html").read_text(encoding="utf-8")
    index_es = (SITE / "index.es.html").read_text(encoding="utf-8")
    if build_site.STORY_SHARE_ENABLED:
        assert 'href="story.html"' in index and 'class="sharebar"' in index
        assert 'href="story.es.html"' in index_es and 'class="sharebar"' in index_es
        assert 'class="sharewrap"' in index and 'class="sharepop"' in index   # masthead share icon
        assert 'class="sharewrap"' in index_es
    else:
        for html in (index, index_es):
            assert 'class="sharebar"' not in html and 'class="sharewrap"' not in html
            assert "story.html" not in html and "story.es.html" not in html


def test_story_share_strings_bilingual_parity():
    """Every STORY_*/SHARE_* key must exist in both languages (the standing 'change both' rule)."""
    keys = {k for k in STRINGS["en"] if k.startswith(("STORY_", "SHARE_"))}
    assert keys, "no STORY_/SHARE_ keys found"
    for lang in LANGS:
        missing = keys - set(STRINGS[lang])
        assert not missing, f"{lang} is missing story/share keys: {sorted(missing)}"
