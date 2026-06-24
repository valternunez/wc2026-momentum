"""Social share card (1200x630 OpenGraph image) + apple-touch icon.

Rendered pixel-perfect in the editorial fonts via Playwright (a real browser, so the
Newsreader/IBM Plex fonts and palette match the site exactly) -> reports/figures/og.png,
committed. CI never regenerates it (no browser); build_site copies it into site/ and the
<head> OG/Twitter tags point at the absolute Pages URL. Run via `pipeline --og-card`.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.paths import PROCESSED, REPORTS, SITE

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
   <div><div class="n alt">{CWC}</div><div class="lbl">with no break (same teams)</div></div>
   <div class="arrow">&rarr; mostly regression to the mean &mdash; but not all</div>
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
   <div><div class="n alt">{CWC}</div><div class="lbl">sin pausa (mismos equipos)</div></div>
   <div class="arrow">&rarr; sobre todo regresión a la media &mdash; pero no todo</div>
 </div>
 <div class="foot"><span><b>Un análisis vivo, basado en datos</b> &middot; FotMob + ESPN</span><span>valternunez.github.io/wc2026-momentum</span></div>
</div></body></html>"""

_ICON = """<!doctype html><html><head><meta charset='utf-8'><style>*{margin:0;padding:0}
body{width:180px;height:180px;background:#1A1813;display:flex;align-items:center;justify-content:center}
.d{width:74px;height:74px;border-radius:50%;background:#E5482E}</style></head><body><div class="d"></div></body></html>"""


def _finding_numbers() -> tuple[str, str]:
    """(break drop, same-teams no-break drop). The no-break number is the within-2026 control
    (the same WC2026 teams windowed at quiet minutes), the cleanest like-for-like baseline."""
    hyd = nobreak = None
    try:
        from src.analysis.descriptive import effect_by_type, load_processed

        eff = {e["stoppage_type"]: e for e in effect_by_type(load_processed())}
        hyd = eff.get("hydration", {}).get("mean_delta")
    except Exception:
        pass
    try:
        import polars as pl

        from src.analysis.descriptive import cluster_bootstrap_ci, on_top_rows

        p = PROCESSED / "placebo2026.parquet"
        if p.exists():
            nobreak, _, _ = cluster_bootstrap_ci(on_top_rows(pl.read_parquet(p)))
    except Exception:
        pass
    return (f"−{abs(hyd):.0f}" if hyd is not None else "−25",
            f"−{abs(nobreak):.0f}" if nobreak is not None else "−17")


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


def build_story_cards() -> str:
    """Render each story slide as a 1080x1920 (Instagram-Story native) still PNG (needs Playwright).

    Opens the already-built site/story.html (EN) + story.es.html (ES) with ?still=N — which freezes
    the page to one slide, final state, no animation — and screenshots the #frame element so each PNG
    is exactly the 9:16 card. Writes reports/figures/story/{en,es}/slide{N}.png, committed; CI (no
    browser) just copies them into site/story/. Run locally after a build via `pipeline --story-cards`.
    Returns the output directory.
    """
    pages = {"en": SITE / "story.html", "es": SITE / "story.es.html"}
    outroot = REPORTS / "figures" / "story"

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for lang, path in pages.items():
            if not path.exists():
                continue
            dest = outroot / lang
            dest.mkdir(parents=True, exist_ok=True)
            base = path.resolve().as_uri()
            # discover the slide count from the live DOM (single source of truth: the template)
            probe = b.new_page(viewport={"width": 1080, "height": 1920})
            probe.goto(f"{base}?still=1", wait_until="networkidle")
            n = int(probe.evaluate("document.querySelectorAll('.slide').length"))
            probe.close()
            for i in range(1, n + 1):
                pg = b.new_page(viewport={"width": 1080, "height": 1920})
                pg.goto(f"{base}?still={i}", wait_until="networkidle")
                pg.wait_for_timeout(900)  # let webfonts swap in
                pg.locator("#frame").screenshot(path=str(dest / f"slide{i}.png"))
                pg.close()
        b.close()
    return str(outroot)


STORY_VIDEO = REPORTS / "figures" / "story.mp4"
STORY_VIDEO_ES = REPORTS / "figures" / "story.es.mp4"
RENDER_STATE = REPORTS / "figures" / "render_state.json"
_AUTOPLAY_PER_MS = 3200  # must match the per-slide timer in story_copy.py ?autoplay mode


def build_story_video() -> str:
    """Render the story as a downloadable 1080x1920 MP4 per language (needs Playwright + ffmpeg).

    Opens the already-built site/story.html?autoplay=1 (auto-advances the slides, chrome hidden) in a
    Playwright context that records video, then transcodes the .webm to a phone-friendly H.264 MP4 via
    the pip-installed static ffmpeg (imageio-ffmpeg) — sized for Instagram Story/Reel + TikTok. Writes
    reports/figures/story.mp4 + story.es.mp4, committed like og.png. Run via `pipeline --story-video`.
    """
    import subprocess
    import tempfile

    import imageio_ffmpeg
    from playwright.sync_api import sync_playwright

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    W, H = 1080, 1920
    pages = {"en": (SITE / "story.html", STORY_VIDEO), "es": (SITE / "story.es.html", STORY_VIDEO_ES)}
    out: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for _lang, (path, dest) in pages.items():
            if not path.exists():
                continue
            base = path.resolve().as_uri()
            probe = b.new_page(viewport={"width": W, "height": H})
            probe.goto(f"{base}?still=1", wait_until="networkidle")
            n = int(probe.evaluate("document.querySelectorAll('.slide').length"))
            probe.close()
            duration = n * _AUTOPLAY_PER_MS + 1600  # advance through every slide, then a brief hold
            with tempfile.TemporaryDirectory() as td:
                ctx = b.new_context(viewport={"width": W, "height": H},
                                    record_video_dir=td,
                                    record_video_size={"width": W, "height": H})
                pg = ctx.new_page()
                pg.goto(f"{base}?autoplay=1", wait_until="networkidle")
                pg.wait_for_timeout(duration)
                pg.close()
                webm = pg.video.path()
                ctx.close()  # flush the webm to disk
                dest.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    [ffmpeg, "-y", "-i", webm, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                     "-r", "30", "-movflags", "+faststart", "-an", str(dest)],
                    check=True, capture_output=True,
                )
            out.append(str(dest))
        b.close()
    return ", ".join(out)


def refresh_social(force: bool = False) -> str:
    """Regenerate the committed social artifacts (og cards + story stills + story videos) IF the
    headline numbers moved since the last render — keeping the downloadable images/video in step with
    the data without churning binaries when nothing changed. Best-effort: if a renderer's deps are
    missing (no browser/ffmpeg) it logs and skips, and the render-state is only advanced when every
    renderer succeeded, so a partial run retries next time. Called by the daily scripts after build."""
    from src.report.build_site import finding_signature

    sig = finding_signature()
    if not sig:
        print("[refresh-social] no processed data; skip")
        return "skip"
    prev = None
    if RENDER_STATE.exists():
        try:
            prev = json.loads(RENDER_STATE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            prev = None
    if prev == sig and not force:
        print("[refresh-social] up to date")
        return "up-to-date"

    done, failed = [], []
    for name, fn in (("og-card", build_share_card),
                     ("story-cards", build_story_cards),
                     ("story-video", build_story_video)):
        try:
            fn()
            done.append(name)
        except Exception as e:  # missing browser/ffmpeg, render error — never break the daily run
            failed.append(name)
            print(f"[refresh-social] {name} skipped: {type(e).__name__}: {e}")
    if failed:
        print(f"[refresh-social] partial render ({', '.join(done) or 'none'}); leaving state for retry")
        return "partial"
    RENDER_STATE.parent.mkdir(parents=True, exist_ok=True)
    RENDER_STATE.write_text(json.dumps(sig, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[refresh-social] rendered: {', '.join(done)}")
    return "rendered"
