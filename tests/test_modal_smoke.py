"""Browser smoke test: clicking a match card opens the modal with no JS errors.

This is the durable guard for the 'clicking a match does nothing' class of bug — a JS
syntax/runtime error in the inline <script> silently kills every click handler, and pure
string assertions on the HTML can't see it. Here we actually load the built page in a real
browser, click the first match card, and assert the modal opens with zero page errors.

Skips cleanly where Playwright or a browser binary isn't available (e.g. CI publish runs),
so it never blocks the offline test suite — it runs locally, where the site is built and
pushed from.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api", reason="playwright not installed")


def _check_page(browser, path: Path) -> None:
    errors: list[str] = []
    page = browser.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(path.resolve().as_uri(), wait_until="networkidle")
    cards = page.locator("[data-mid]")
    assert cards.count() > 0, f"no match cards on {path.name}"
    cards.first.click()
    page.wait_for_timeout(300)
    assert not errors, f"JS page error(s) on {path.name}: {errors}"
    # modal un-hides only if open() ran to completion (chrome()/render() didn't throw)
    assert page.locator("#mb-modal").get_attribute("hidden") is None, f"modal did not open on {path.name}"
    assert page.locator("#mb-title").inner_text().strip(), f"modal title empty on {path.name}"
    page.close()


def test_match_click_opens_modal():
    from src.report import build_site

    en = Path(build_site.build())  # writes index.html (returned) + index.es.html sibling
    if "No data yet" in en.read_text(encoding="utf-8"):
        pytest.skip("no processed data committed")
    es = en.with_name("index.es.html")

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:  # browser binary not installed in this env
                pytest.skip(f"no chromium binary: {e}")
            try:
                _check_page(browser, en)
                if es.exists():
                    _check_page(browser, es)
            finally:
                browser.close()
    except Exception as e:
        # playwright present but driver/host can't run (e.g. sandbox) — don't fail the suite
        if "executable" in str(e).lower() or "install" in str(e).lower():
            pytest.skip(f"playwright runtime unavailable: {e}")
        raise
