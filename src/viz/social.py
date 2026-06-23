"""Social share card (1200x630 OpenGraph image) + apple-touch icon.

Rendered pixel-perfect in the editorial fonts via Playwright (a real browser, so the
Newsreader/IBM Plex fonts and palette match the site exactly) -> reports/figures/og.png,
committed. CI never regenerates it (no browser); build_site copies it into site/ and the
<head> OG/Twitter tags point at the absolute Pages URL. Run via `pipeline --og-card`.
"""

from __future__ import annotations

from pathlib import Path

from src.paths import PROCESSED, REPORTS

OUT = REPORTS / "figures" / "og.png"
OUT_ES = REPORTS / "figures" / "og.es.png"

_CARD = """<!doctype html><html><head><meta charset='utf-8'>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@500;600&display=swap" rel="stylesheet">
<style>
 *{margin:0;padding:0;box-sizing:border-box}
 body{width:1200px;height:630px;background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif;overflow:hidden}
 .wrap{padding:64px 70px;height:100%;display:flex;flex-direction:column;justify-content:space-between}
 .kick{font-family:'IBM Plex Mono',monospace;font-size:18px;letter-spacing:.22em;text-transform:uppercase;color:#E5482E;font-weight:600}
 h1{font-family:'Newsreader',serif;font-weight:500;font-size:72px;line-height:1.0;letter-spacing:-.015em;max-width:18ch;margin-top:8px}
 .nums{display:flex;align-items:flex-start;gap:46px;margin-top:10px}
 .n{font-family:'Newsreader',serif;font-weight:500;font-size:104px;line-height:.9;color:#E5482E}
 .n.alt{color:#1A1813}
 .lbl{font-family:'IBM Plex Mono',monospace;font-size:15px;letter-spacing:.04em;color:#46412F;margin-top:8px;max-width:16ch}
 .arrow{font-family:'Newsreader',serif;font-style:italic;font-size:30px;color:#1A1813;align-self:center;max-width:13ch;line-height:1.25}
 .foot{display:flex;justify-content:space-between;align-items:center;border-top:2px solid #1A1813;padding-top:20px;font-family:'IBM Plex Mono',monospace;font-size:16px;letter-spacing:.06em;color:#6B6557}
 .foot b{color:#1A1813}
</style></head><body><div class="wrap">
 <div>
   <div class="kick">WC2026 · Stoppage Momentum Study</div>
   <h1>Do hydration breaks really kill momentum?</h1>
 </div>
 <div class="nums">
   <div><div class="n">{HYD}</div><div class="lbl">momentum after a break</div></div>
   <div><div class="n alt">{CWC}</div><div class="lbl">with NO break (2025 CWC)</div></div>
   <div class="arrow">&rarr; it's mostly regression to the mean</div>
 </div>
 <div class="foot"><span><b>A living, data-driven analysis</b> &middot; FotMob + ESPN</span><span>valternunez.github.io/wc2026-momentum</span></div>
</div></body></html>"""

# Spanish share card — same layout, translated copy. Rendered to og.es.png; the ES page
# (index.es.html) points its OG/Twitter tags at it.
_CARD_ES = """<!doctype html><html><head><meta charset='utf-8'>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@500;600&display=swap" rel="stylesheet">
<style>
 *{margin:0;padding:0;box-sizing:border-box}
 body{width:1200px;height:630px;background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif;overflow:hidden}
 .wrap{padding:64px 70px;height:100%;display:flex;flex-direction:column;justify-content:space-between}
 .kick{font-family:'IBM Plex Mono',monospace;font-size:18px;letter-spacing:.22em;text-transform:uppercase;color:#E5482E;font-weight:600}
 h1{font-family:'Newsreader',serif;font-weight:500;font-size:66px;line-height:1.0;letter-spacing:-.015em;max-width:19ch;margin-top:8px}
 .nums{display:flex;align-items:flex-start;gap:46px;margin-top:10px}
 .n{font-family:'Newsreader',serif;font-weight:500;font-size:104px;line-height:.9;color:#E5482E}
 .n.alt{color:#1A1813}
 .lbl{font-family:'IBM Plex Mono',monospace;font-size:15px;letter-spacing:.04em;color:#46412F;margin-top:8px;max-width:16ch}
 .arrow{font-family:'Newsreader',serif;font-style:italic;font-size:30px;color:#1A1813;align-self:center;max-width:14ch;line-height:1.25}
 .foot{display:flex;justify-content:space-between;align-items:center;border-top:2px solid #1A1813;padding-top:20px;font-family:'IBM Plex Mono',monospace;font-size:16px;letter-spacing:.06em;color:#6B6557}
 .foot b{color:#1A1813}
</style></head><body><div class="wrap">
 <div>
   <div class="kick">WC2026 · Estudio de Momentum en Pausas</div>
   <h1>¿Las pausas de hidratación matan el momentum?</h1>
 </div>
 <div class="nums">
   <div><div class="n">{HYD}</div><div class="lbl">de momentum tras una pausa</div></div>
   <div><div class="n alt">{CWC}</div><div class="lbl">SIN pausa (Mundial Clubes 2025)</div></div>
   <div class="arrow">&rarr; es sobre todo regresión a la media</div>
 </div>
 <div class="foot"><span><b>Un análisis vivo, basado en datos</b> &middot; FotMob + ESPN</span><span>valternunez.github.io/wc2026-momentum</span></div>
</div></body></html>"""

_ICON = """<!doctype html><html><head><meta charset='utf-8'><style>*{margin:0;padding:0}
body{width:180px;height:180px;background:#1A1813;display:flex;align-items:center;justify-content:center}
.d{width:74px;height:74px;border-radius:50%;background:#E5482E}</style></head><body><div class="d"></div></body></html>"""


def _finding_numbers() -> tuple[str, str]:
    hyd = cwc = None
    try:
        from src.analysis.descriptive import effect_by_type, load_processed

        eff = {e["stoppage_type"]: e for e in effect_by_type(load_processed())}
        hyd = eff.get("hydration", {}).get("mean_delta")
    except Exception:
        pass
    try:
        import polars as pl

        from src.analysis.descriptive import cluster_bootstrap_ci, on_top_rows

        p = PROCESSED / "cwc2025_placebo.parquet"
        if p.exists():
            cwc, _, _ = cluster_bootstrap_ci(on_top_rows(pl.read_parquet(p)))
    except Exception:
        pass
    return (f"−{abs(hyd):.0f}" if hyd is not None else "−24",
            f"−{abs(cwc):.0f}" if cwc is not None else "−23")


def build_share_card(out_path: str | Path | None = None) -> str:
    """Render the EN + ES 1200x630 share cards + 180px touch icon (needs Playwright).

    Writes og.png (English) and og.es.png (Spanish) next to each other, plus the shared
    apple-touch-icon.png. Returns the English og path.
    """
    out = Path(out_path or OUT)
    out_es = out.parent / OUT_ES.name
    out.parent.mkdir(parents=True, exist_ok=True)
    hyd, cwc = _finding_numbers()
    html_en = _CARD.replace("{HYD}", hyd).replace("{CWC}", cwc)
    html_es = _CARD_ES.replace("{HYD}", hyd).replace("{CWC}", cwc)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for card_html, dest in ((html_en, out), (html_es, out_es)):
            pg = b.new_page(viewport={"width": 1200, "height": 630})
            pg.set_content(card_html, wait_until="networkidle")
            pg.wait_for_timeout(1200)  # let webfonts swap in
            pg.screenshot(path=str(dest), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
            pg.close()
        pi = b.new_page(viewport={"width": 180, "height": 180})
        pi.set_content(_ICON, wait_until="domcontentloaded")
        pi.wait_for_timeout(150)
        pi.screenshot(path=str(out.parent / "apple-touch-icon.png"))
        b.close()
    return str(out)
