"""Render the methodology page to a downloadable long-form PDF (local-only, committed).

Mirrors viz/social.py + the og.png pattern: a headless Chromium loads the already-built
site/method.html and site/method.es.html via file://, applies print media (the page's
@media print stylesheet flattens it), and writes the PDFs to reports/figures/ — the COMMITTED
artifact location. CI has no browser, so build_site.build() copies them into the (gitignored)
site/ on every deploy, exactly like og.png. Regenerate locally when the method copy changes:
  uv run python -m src.report.build_site && uv run python -m src.pipeline --method-pdf
"""

from __future__ import annotations

from src.paths import REPORTS, SITE

OUTDIR = REPORTS / "figures"
# (built page in site/, committed pdf name served from the site root)
PAGES = [("method.html", "wc2026-methodology.pdf"), ("method.es.html", "wc2026-methodology.es.pdf")]


def build_methodology_pdf() -> list[str]:
    """Render both language method pages to committed PDFs in reports/figures/. Returns paths.

    Requires the method pages to exist (run build_site first) and Playwright + a Chromium
    binary (local only). Raises if the pages are missing so the caller fails loudly.
    """
    missing = [name for name, _ in PAGES if not (SITE / name).exists()]
    if missing:
        raise FileNotFoundError(f"build the site first — missing {missing} (run build_site)")

    from playwright.sync_api import sync_playwright

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for src_name, pdf_name in PAGES:
            page = browser.new_page()
            page.goto((SITE / src_name).resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.wait_for_timeout(500)  # let webfonts swap in before the snapshot
            dest = OUTDIR / pdf_name
            page.pdf(path=str(dest), prefer_css_page_size=True, print_background=False)
            page.close()
            out.append(str(dest))
        browser.close()
    return out


if __name__ == "__main__":
    for p in build_methodology_pdf():
        print("[method-pdf]", p)
