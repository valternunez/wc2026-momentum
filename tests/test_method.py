"""Tests for the bilingual methodology / full-report page (method.html + method.es.html)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.paths import PROCESSED, SITE
from src.report import build_site


def _build_pages() -> tuple[str, str] | None:
    """Build the site; return (en, es) method HTML or None if no data is committed."""
    index = Path(build_site.build())
    if "No data yet" in index.read_text(encoding="utf-8"):
        return None
    en = (SITE / "method.html").read_text(encoding="utf-8")
    es = (SITE / "method.es.html").read_text(encoding="utf-8")
    return en, es


def test_method_pages_built_and_resolved():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    en, es = pages
    for html in (en, es):
        assert "{{" not in html              # every token substituted (also guarded in build())
        assert "<!DOCTYPE html>" in html
    # findings-first so the page doubles as a report; the headline numbers are present
    assert "Findings in brief" in en and "regression to the mean" in en
    assert "Los hallazgos, en breve" in es and "regresión a la media" in es
    # the heat/acclimatization section the §06 caveat links to
    assert 'id="heat"' in en and 'id="heat"' in es
    assert "acclimatization" in en.lower() and "aclimatación" in es.lower()
    # honest limits + reproducibility
    assert "can and cannot say" in en and "Reproducibility" in en
    assert "github.com/valternunez/wc2026-momentum" in en and "github.com/valternunez/wc2026-momentum" in es


def test_method_links_and_pdf():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    en, es = pages
    # back-link to the story + same-language PDF download
    assert 'href="index.html"' in en and "← The story" in en
    assert 'href="index.es.html"' in es and "← El reportaje" in es
    assert 'href="wc2026-methodology.pdf"' in en
    assert 'href="wc2026-methodology.es.pdf"' in es
    # language toggle stays within the method family (not back to index)
    assert 'href="method.es.html"' in en     # EN page links to ES sibling
    assert 'href="method.html"' in es        # ES page links to EN sibling


def test_main_page_links_to_methodology():
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    index = (SITE / "index.html").read_text(encoding="utf-8")
    index_es = (SITE / "index.es.html").read_text(encoding="utf-8")
    # masthead/footer link to the method page + the §06 acclimatization caveat links to #heat
    assert 'href="method.html"' in index and "Methodology" in index
    assert "method.html#heat" in index       # §06 "How we tested it" link
    assert 'href="method.es.html"' in index_es and "Metodología" in index_es
    assert "method.es.html#heat" in index_es


def test_accl_numbers_present_not_placeholder():
    """The heat table should carry real figures (acclimatization.parquet is committed)."""
    pages = _build_pages()
    if pages is None:
        pytest.skip("no processed data committed")
    en, _ = pages
    if not (PROCESSED / "acclimatization.parquet").exists():
        pytest.skip("acclimatization parquet not present")
    # the per-tournament heat-gap table resolved to numbers (°C cells), not em-dashes
    import re

    assert re.search(r"[+-]\d+°C</td><td>[+-]\d+", en), "acclimatization table did not resolve to numbers"
