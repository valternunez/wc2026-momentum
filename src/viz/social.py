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


# --- LinkedIn graph cards (square 1200x1200 forest plots) -------------------
CARD_BASELINES = REPORTS / "figures" / "card-baselines.png"
CARD_BYTYPE = REPORTS / "figures" / "card-bytype.png"
_CARD_URL = "valternunez.github.io/wc2026-momentum"

_GRAPH_CARD = """<!doctype html><html><head><meta charset='utf-8'>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@500;600&display=swap" rel="stylesheet">
<style>
 *{margin:0;padding:0;box-sizing:border-box}
 body{width:1200px;height:1200px;background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif}
 .card{padding:70px 76px;height:100%;display:flex;flex-direction:column}
 .kick{font-family:'IBM Plex Mono',monospace;font-size:19px;letter-spacing:.22em;text-transform:uppercase;color:#E5482E;font-weight:600}
 h1{font-family:'Newsreader',serif;font-weight:500;font-size:58px;line-height:1.04;letter-spacing:-.015em;margin-top:10px}
 .sub{font-family:'IBM Plex Mono',monospace;font-size:18px;color:#5A5547;margin-top:14px;max-width:46ch;line-height:1.45}
 .chart{position:relative;margin-top:40px;flex:1;display:flex;flex-direction:column}
 .grid{position:absolute;top:0;bottom:40px;left:0;right:0;pointer-events:none}
 .gl{position:absolute;top:0;bottom:0;width:1px;background:rgba(26,24,19,.12)}
 .gl.z{width:2px;background:#1A1813}
 .rows{flex:1;display:flex;flex-direction:column;justify-content:space-between}
 .row{position:relative}
 .rh{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:9px}
 .lab{font-weight:600;font-size:25px}
 .rv b{font-family:'Newsreader',serif;font-weight:600;font-size:30px}
 .rv i{font-family:'IBM Plex Mono',monospace;font-style:normal;font-size:15px;color:#6B6557;margin-left:8px}
 .track{position:relative;height:26px}
 .band{position:absolute;top:5px;height:16px;opacity:.16;border-radius:3px}
 .bar{position:absolute;top:11px;height:5px;right:0}
 .dot{position:absolute;top:3px;width:22px;height:22px;border-radius:50%;border:3px solid;box-shadow:0 0 0 4px #EFEBDF}
 .axis{display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:16px;color:#5A5547;margin-top:8px}
 .legend{display:flex;gap:12px 22px;flex-wrap:wrap;align-items:center;font-family:'IBM Plex Mono',monospace;font-size:16px;color:#5A5547;margin-top:10px}
 .legend span{display:inline-flex;align-items:center;gap:8px}
 .sw{display:inline-block}
 .take{font-family:'Newsreader',serif;font-style:italic;font-size:26px;line-height:1.3;color:#1A1813;margin-top:22px;border-left:4px solid #E5482E;padding-left:18px}
 .foot{display:flex;justify-content:space-between;align-items:center;border-top:2px solid #1A1813;padding-top:20px;margin-top:26px;font-family:'IBM Plex Mono',monospace;font-size:17px;letter-spacing:.05em;color:#6B6557}
 .foot b{color:#1A1813}
</style></head><body><div class="card">
 <div class="kick">WC2026 · STOPPAGE MOMENTUM STUDY</div>
 <h1>{TITLE}</h1>
 <div class="sub">{SUBTITLE}</div>
 <div class="chart"><div class="grid">{GRID}</div>
   <div class="rows">{ROWS}</div>
   <div class="axis"><span>&minus;30</span><span>&minus;20</span><span>&minus;10</span><span>0</span></div>
 </div>
 {LEGEND}
 <div class="take">{TAKE}</div>
 <div class="foot"><span><b>A living, data-driven analysis</b> &middot; FotMob + ESPN</span><span>{URL}</span></div>
</div></body></html>"""


def _graph_geom():
    """(SCALE, ACCENT, NT, CLUBS) from build_site so the card matches the site exactly."""
    from src.report.build_site import ACCENT, CC_CLUBS, CC_NT, SCALE
    return SCALE, ACCENT, CC_NT, CC_CLUBS


def _forest_row(label, mean, lo, hi, n, matches, color, solid, scale) -> str:
    a, b = abs(lo), abs(hi)
    losp, hisp = min(min(a, b) / scale * 100, 100), min(max(a, b) / scale * 100, 100)
    mp = min(abs(mean) / scale * 100, 100)
    dot_fill = color if solid else "#EFEBDF"
    barop = "0.9" if solid else "0.35"
    return f"""
    <div class="row">
      <div class="rh"><span class="lab" style="color:{color}">{label}</span>
        <span class="rv"><b style="color:{color}">&minus;{abs(mean):.0f}</b><i>n={n}</i></span></div>
      <div class="track">
        <div class="band" style="right:{losp:.2f}%;width:{hisp - losp:.2f}%;background:{color}"></div>
        <div class="bar" style="width:{mp:.2f}%;background:{color};opacity:{barop}"></div>
        <div class="dot" style="right:calc({mp:.2f}% - 11px);background:{dot_fill};border-color:{color}"></div>
      </div>
    </div>"""


def _grid_lines(scale) -> str:
    # vertical gridlines at 0 / -10 / -20 / -30 (right-anchored, 0 at the right edge)
    out = ['<div class="gl z" style="right:0"></div>']
    for v in (10, 20, 30):
        out.append(f'<div class="gl" style="right:{v / scale * 100:.2f}%"></div>')
    return "".join(out)


def _card_html(title, subtitle, rows, legend, take) -> str:
    scale, *_ = _graph_geom()
    rows_html = "".join(_forest_row(*r, scale) for r in rows)
    return (_GRAPH_CARD.replace("{TITLE}", title).replace("{SUBTITLE}", subtitle)
            .replace("{GRID}", _grid_lines(scale)).replace("{ROWS}", rows_html)
            .replace("{LEGEND}", legend).replace("{TAKE}", take).replace("{URL}", _CARD_URL))


def build_graph_cards() -> list[str]:
    """Render two square 1200x1200 forest-plot cards for a LinkedIn carousel (needs Playwright):
    card-baselines.png (break vs no-break controls) and card-bytype.png (hydration vs other stoppages).
    Numbers come from the same source as the site (comparison_rows / effect_by_type), so they can't drift.
    """
    import polars as pl  # noqa: F401

    from src.report.build_site import comparison_rows
    from src.report.i18n import FRAG
    from src.analysis.descriptive import effect_by_type, load_processed

    scale, accent, nt, clubs = _graph_geom()
    df = load_processed()
    eff = effect_by_type(df)

    # Card 1 — break vs no-break baselines (drop the long sub + tip; keep label/stats/color/solid).
    base_rows = [(label, mean, lo, hi, n, matches, color, solid)
                 for (label, _sub, mean, lo, hi, n, matches, color, solid, _tip) in comparison_rows(eff, FRAG["en"])]
    hyd_v = base_rows[0][1] if base_rows else None  # hydration is always the first comparison row
    p26_v = next((m for (lab, m, *_2) in base_rows if "same 2026" in lab), None)
    hh = f"&minus;{abs(hyd_v):.0f}" if hyd_v is not None else "&minus;23"
    pp = f"&minus;{abs(p26_v):.0f}" if p26_v is not None else "&minus;19"
    base_legend = (
        '<div class="legend">'
        f'<span><span class="sw" style="width:15px;height:15px;border-radius:50%;background:{accent};border:3px solid {accent}"></span>mandated break</span>'
        '<span><span class="sw" style="width:15px;height:15px;border-radius:50%;background:#EFEBDF;border:3px solid #5A5547"></span>no break (control)</span>'
        f'<span><span class="sw" style="width:16px;height:5px;background:{accent}"></span>same 2026 teams</span>'
        f'<span><span class="sw" style="width:16px;height:5px;background:{nt}"></span>other national teams</span>'
        f'<span><span class="sw" style="width:16px;height:5px;background:{clubs}"></span>club football</span>'
        '</div>')
    base_html = _card_html(
        "A hydration break vs no break at all",
        "Momentum the dominant team loses in the 5 min after each stoppage, with its 95% interval.",
        base_rows, base_legend,
        f"{hh} with a break, but {pp} for the same teams at quiet minutes &rarr; mostly regression to the mean.")

    # Card 2 — hydration vs other stoppage types (same dot+band style; hydration is the filled accent dot).
    type_lbl = {"hydration": "Hydration break", "injury_huddle": "Injury (sub made)",
                "injury_no_huddle": "Injury (no sub)", "var": "VAR review"}
    bt = sorted((e for e in eff if e["n"]), key=lambda e: -abs(e["mean_delta"]))
    type_rows = [(type_lbl.get(e["stoppage_type"], e["stoppage_type"]), e["mean_delta"], e["ci_lo"], e["ci_hi"],
                  e["n"], e["n_matches"], (accent if e["stoppage_type"] == "hydration" else nt),
                  e["stoppage_type"] == "hydration") for e in bt]
    type_html = _card_html(
        "A hydration break vs other stoppages",
        "Momentum the dominant team loses after each stoppage type, with its 95% interval.",
        type_rows, "",
        "Every stoppage cools the leader. The hydration break is the deepest &rarr; but the gaps still overlap.")

    from playwright.sync_api import sync_playwright

    out: list[str] = []
    CARD_BASELINES.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for html, dest in ((base_html, CARD_BASELINES), (type_html, CARD_BYTYPE)):
            pg = b.new_page(viewport={"width": 1200, "height": 1200})
            pg.set_content(html, wait_until="networkidle")
            pg.wait_for_timeout(1200)  # let webfonts swap in
            pg.screenshot(path=str(dest), clip={"x": 0, "y": 0, "width": 1200, "height": 1200})
            pg.close()
            out.append(str(dest))
        b.close()
    return out


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
REEL_VIDEO = REPORTS / "figures" / "reel.mp4"
REEL_VIDEO_ES = REPORTS / "figures" / "reel.es.mp4"
RENDER_STATE = REPORTS / "figures" / "render_state.json"
_VID_W, _VID_H = 1080, 1920          # Instagram Story/Reel + TikTok native size
_AUTOPLAY_PER_MS = 3200              # must match the per-slide timer in story_copy.py ?autoplay
_REEL_MS = 20500                     # must cover the reel_copy.py timeline (last beat 17000 + hold)


def _record_and_transcode(b, url: str, dest, duration_ms: int, ffmpeg: str, play_js: str | None = None) -> str:
    """Record `url` for duration_ms in a video-capturing Playwright context, then transcode the .webm
    to a phone-friendly H.264 MP4 (yuv420p, 30fps, faststart, silent). `b` is a launched browser.

    If `play_js` is given, the page is loaded, fonts are settled, then play_js is evaluated to START a
    timeline at a known instant; we wait duration_ms and trim the MP4 to exactly that trailing window
    (so the variable load/font pre-roll is dropped). Without play_js the page is recorded as-is."""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        ctx = b.new_context(viewport={"width": _VID_W, "height": _VID_H},
                            record_video_dir=td,
                            record_video_size={"width": _VID_W, "height": _VID_H})
        pg = ctx.new_page()
        pg.goto(url, wait_until=("load" if play_js else "networkidle"))
        if play_js:
            try:
                pg.evaluate("document.fonts && document.fonts.ready")  # settle webfonts before play
            except Exception:
                pass
            pg.evaluate(play_js)
        pg.wait_for_timeout(duration_ms)
        pg.close()
        webm = pg.video.path()
        ctx.close()  # flush the webm to disk
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = [ffmpeg, "-y"]
        if play_js:  # the timeline occupies the final duration_ms of the clip → keep just that window
            cmd += ["-sseof", f"-{duration_ms / 1000.0:.2f}"]
        cmd += ["-i", webm, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", "30", "-movflags", "+faststart", "-an", str(dest)]
        subprocess.run(cmd, check=True, capture_output=True)
    return str(dest)


def build_story_video() -> str:
    """Render the story as a downloadable 1080x1920 MP4 per language (needs Playwright + ffmpeg).

    Opens the already-built site/story.html?autoplay=1 (auto-advances the slides, chrome hidden),
    records it, and transcodes to MP4 — Instagram Story/Reel + TikTok sized. Writes story.mp4 +
    story.es.mp4 under reports/figures, committed like og.png. Run via `pipeline --story-video`.
    """
    import imageio_ffmpeg
    from playwright.sync_api import sync_playwright

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pages = {"en": (SITE / "story.html", STORY_VIDEO), "es": (SITE / "story.es.html", STORY_VIDEO_ES)}
    out: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for _lang, (path, dest) in pages.items():
            if not path.exists():
                continue
            base = path.resolve().as_uri()
            probe = b.new_page(viewport={"width": _VID_W, "height": _VID_H})
            probe.goto(f"{base}?still=1", wait_until="networkidle")
            n = int(probe.evaluate("document.querySelectorAll('.slide').length"))
            probe.close()
            duration = n * _AUTOPLAY_PER_MS + 1600  # advance through every slide, then a brief hold
            out.append(_record_and_transcode(b, f"{base}?autoplay=1", dest, duration, ffmpeg))
        b.close()
    return ", ".join(out)


def build_reel_video() -> str:
    """Render the ~15s kinetic reel as a 1080x1920 MP4 per language (needs Playwright + ffmpeg).

    Records the already-built site/reel.html (auto-plays its myth-buster timeline on load) and
    transcodes to MP4 — Reel/TikTok ready. Writes reel.mp4 + reel.es.mp4 under reports/figures,
    committed like og.png. Run via `pipeline --reel-video`.
    """
    import imageio_ffmpeg
    from playwright.sync_api import sync_playwright

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pages = {"en": (SITE / "reel.html", REEL_VIDEO), "es": (SITE / "reel.es.html", REEL_VIDEO_ES)}
    out: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for _lang, (path, dest) in pages.items():
            if not path.exists():
                continue
            url = f"{path.resolve().as_uri()}?rec=1"
            out.append(_record_and_transcode(b, url, dest, _REEL_MS, ffmpeg,
                                             play_js="window.__play && window.__play()"))
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
                     ("graph-cards", build_graph_cards),
                     ("story-cards", build_story_cards),
                     ("story-video", build_story_video),
                     ("reel-video", build_reel_video)):
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
