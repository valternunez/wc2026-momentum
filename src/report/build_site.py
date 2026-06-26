"""Build the editorial report from the committed dataset, in English + Spanish.

Renders the editorial design (src/report/editorial_copy.TEMPLATE) by substituting {{TOKENS}}
with values computed live from data/processed/*. All human copy lives in src/report/i18n.py;
this module selects each language, fills the prose + data tokens, and writes a sibling file:
EN -> site/index.html, ES -> site/index.es.html (relative asset paths stay valid either way).
CI-safe: only base deps (polars/numpy/scipy) — no scraping, no pandas/statsmodels. Per-match
panel images are generated locally and committed; here we just copy and embed them.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import polars as pl

from src.analysis.descriptive import (
    cluster_bootstrap_ci,
    effect_by_type,
    load_processed,
    on_top_rows,
    pre_level_r2,
)
from src.enrich.venues import venue_elev_m
from src.paths import PROCESSED, RAW, REPORTS, SITE, STOPPAGES_PARQUET
from src.report.editorial_copy import TEMPLATE
from src.report.i18n import COUNTRIES, FRAG, JS, LABELS, LANGS, MONTHS, STAGE, STRINGS, TYPES
from src.snapshot import load_all_snapshots

ACCENT = "#E5482E"
INK = "#1A1813"
SCALE = 32.0  # momentum axis: 0 .. -32
PAGES_URL = "https://github.com/valternunez/wc2026-momentum"
SITE_BASE = "https://valternunez.github.io/wc2026-momentum/"

# Temporarily hide the Story-mode + Share entry points on the MAIN page (masthead Story link +
# share icon, bottom "Open story" button + share bar). The story/reel pages and all the code stay
# built and intact — flip this back to True to restore the entry points. See the project memory note.
STORY_SHARE_ENABLED = False

_ORDER = ["hydration", "var", "injury_huddle", "injury_no_huddle"]
_KO_ORDER = {"1/16": 1, "1/8": 2, "1/4": 3, "1/2": 4, "bronze": 5, "final": 6}
UNKNOWN_TEAM = "?"  # single placeholder for a missing team name (used everywhere)

# Per-language <head> meta + output filename. Sibling files keep relative asset paths valid.
_LANG_META = {
    "en": {"LANG": "en", "OG_LOCALE": "en_US", "CANONICAL_URL": SITE_BASE,
           "OG_URL": SITE_BASE, "OG_IMAGE": SITE_BASE + "og.png"},
    "es": {"LANG": "es", "OG_LOCALE": "es_MX", "CANONICAL_URL": SITE_BASE + "index.es.html",
           "OG_URL": SITE_BASE + "index.es.html", "OG_IMAGE": SITE_BASE + "og.es.png"},
}
_OUTFILE = {"en": "index.html", "es": "index.es.html"}


def _team(name: str, lang: str) -> str:
    """Country/team name in `lang` (Spanish via COUNTRIES; English passes through unchanged)."""
    return COUNTRIES.get(name, name) if lang == "es" else name


def _fmt_date_iso(iso: str | None, lang: str) -> str:
    """ISO date (YYYY-MM-DD) → '22 jun 2026' in `lang` (falls back to today on missing/bad input)."""
    months = MONTHS[lang]
    d = None
    if iso:
        try:
            d = datetime.strptime(iso, "%Y-%m-%d")
        except (TypeError, ValueError):
            d = None
    if d is None:
        d = datetime.now(timezone.utc)
    return f"{d.day} {months[d.month]} {d.year}"


def _page_link(target: str, lang: str) -> str:
    """Same-language sibling filename for a page family ('index'/'method'). ES adds '.es'."""
    return f"{target}.html" if lang == "en" else f"{target}.es.html"


def _lang_toggle(lang: str, page: str = "index") -> str:
    """Footer English ⇄ Español switch within the current page family (index/method).
    The current language is inert, the other links to its sibling file."""
    base = "font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em"
    on = f"{base};color:#E5C9A0;font-weight:600"
    off = f"{base};color:#7E776A;text-decoration:none;border-bottom:1px solid rgba(229,72,46,.35)"
    en = (f'<span style="{on}">English</span>' if lang == "en"
          else f'<a class="same-tab" href="{page}.html" style="{off}">English</a>')
    es = (f'<span style="{on}">Español</span>' if lang == "es"
          else f'<a class="same-tab" href="{page}.es.html" style="{off}">Español</a>')
    sep = f'<span style="{base};color:#5A5547;padding:0 8px">·</span>'
    return f'<div style="margin:0 0 18px">{en}{sep}{es}</div>'


def _share_intents(S: dict, url: str) -> dict:
    """The WhatsApp / X / Telegram web share-intent URLs for a page (one source of truth, reused
    by the bottom share bar and the masthead share icon). Note: Instagram has no web share-intent —
    it is reached via the native OS sheet / the 9:16 image, not a link."""
    text = S["SHARE_TEXT"]
    qtext, qurl = quote(text), quote(url)
    return {
        "text": text,
        "wa": f"https://wa.me/?text={quote(text + ' ' + url)}",
        "x": f"https://twitter.com/intent/tweet?text={qtext}&url={qurl}",
        "tg": f"https://t.me/share/url?url={qurl}&text={qtext}",
    }


def _share_bar(S: dict, url: str) -> str:
    """One-tap share row: WhatsApp / X / Telegram URL-intents (work on desktop + mobile) + a
    copy-link button and a native OS share-sheet button (shown only where navigator.share exists,
    which is how Instagram/Messages are reached). All labels localized via STRINGS[lang]. The HTML
    is fully inline-styled so it renders the same on the main page and the story CTA slide; a small
    self-contained script wires copy + native."""
    it = _share_intents(S, url)
    text, wa, x, tg = it["text"], it["wa"], it["x"], it["tg"]
    btn = ("display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.02em;"
           "line-height:1;color:#EFEBDF;background:#1A1813;text-decoration:none;padding:8px 12px;"
           "border-radius:4px;border:0;cursor:pointer")
    ghost = ("display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.02em;"
             "line-height:1;color:#46412F;background:none;text-decoration:none;padding:7px 11px;"
             "border-radius:4px;border:1px solid rgba(70,65,47,.4);cursor:pointer")
    lbl = ("font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.14em;"
           "text-transform:uppercase;color:#6B6557")
    a = 'target="_blank" rel="noopener noreferrer"'
    return (
        '<div class="sharebar" style="display:flex;align-items:center;flex-wrap:wrap;gap:9px;margin-top:14px">'
        f'<span style="{lbl}">{html.escape(S["SHARE_LABEL"])}</span>'
        f'<a class="no-nav" style="{btn}" href="{html.escape(wa, quote=True)}" {a}>{html.escape(S["SHARE_WHATSAPP"])}</a>'
        f'<a class="no-nav" style="{btn}" href="{html.escape(x, quote=True)}" {a}>{html.escape(S["SHARE_X"])}</a>'
        f'<a class="no-nav" style="{btn}" href="{html.escape(tg, quote=True)}" {a}>{html.escape(S["SHARE_TELEGRAM"])}</a>'
        f'<button type="button" class="no-nav" style="{ghost}" data-copy="{html.escape(url, quote=True)}" '
        f'data-copied="{html.escape(S["SHARE_COPIED"], quote=True)}">{html.escape(S["SHARE_COPY"])}</button>'
        f'<button type="button" class="no-nav" hidden style="{ghost}" data-native '
        f'data-title="{html.escape(S["SHARE_TITLE"], quote=True)}" data-text="{html.escape(text, quote=True)}" '
        f'data-url="{html.escape(url, quote=True)}">{html.escape(S["SHARE_NATIVE"])}</button>'
        '</div>'
        "<script>(function(){var bars=document.querySelectorAll('.sharebar');"
        "for(var i=0;i<bars.length;i++){(function(bar){"
        "var cp=bar.querySelector('[data-copy]');"
        "if(cp){cp.addEventListener('click',function(){var u=cp.getAttribute('data-copy');"
        "function done(){var t=cp.getAttribute('data-copied')||'Copied';var o=cp.textContent;"
        "cp.textContent=t;setTimeout(function(){cp.textContent=o;},1600);}"
        "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(u).then(done).catch(done);}else{done();}});}"
        "var nt=bar.querySelector('[data-native]');"
        "if(nt&&navigator.share){nt.hidden=false;nt.addEventListener('click',function(){"
        "navigator.share({title:nt.getAttribute('data-title'),text:nt.getAttribute('data-text'),url:nt.getAttribute('data-url')}).catch(function(){});});}"
        "})(bars[i]);}})();</script>"
    )


def _share_button(S: dict, url: str) -> str:
    """Compact share icon for the masthead. On mobile (navigator.share) a tap opens the native OS
    sheet — the path to Instagram / TikTok / WhatsApp / Messages. On desktop it toggles a small
    popover with the WhatsApp / X / Telegram / copy-link intents (closes on Esc / outside-click).
    Self-contained markup + script; reuses the shared intent URLs."""
    it = _share_intents(S, url)
    text, wa, x, tg = it["text"], it["wa"], it["x"], it["tg"]
    icon = ("<svg viewBox='0 0 24 24' width='17' height='17' fill='none' stroke='currentColor' "
            "stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
            "<path d='M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7'/><path d='M12 15V3'/>"
            "<path d='M8 7l4-4 4 4'/></svg>")
    bs = ("display:inline-flex;align-items:center;justify-content:center;min-width:30px;min-height:30px;"
          "padding:6px;background:none;border:0;cursor:pointer;color:#6B6557;border-radius:4px")
    item = ("display:block;font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.02em;"
            "color:#1A1813;text-decoration:none;padding:8px 12px;border-radius:4px;text-align:left;"
            "background:none;border:0;width:100%;cursor:pointer")
    pop = ("position:absolute;top:calc(100% + 8px);right:0;z-index:50;min-width:158px;background:#FCFAF3;"
           "border:1px solid #E0DAC9;border-radius:6px;box-shadow:0 14px 40px rgba(26,24,19,.22);padding:5px")
    a = 'target="_blank" rel="noopener noreferrer" role="menuitem"'
    return (
        '<div class="sharewrap" style="position:relative;display:inline-flex">'
        f'<button type="button" class="sharebtn no-nav" aria-label="{html.escape(S["SHARE_LABEL"], quote=True)}" '
        f'aria-haspopup="true" aria-expanded="false" style="{bs}" '
        f'data-title="{html.escape(S["SHARE_TITLE"], quote=True)}" data-text="{html.escape(text, quote=True)}" '
        f'data-url="{html.escape(url, quote=True)}">{icon}</button>'
        f'<div class="sharepop" hidden role="menu" style="{pop}">'
        f'<a style="{item}" href="{html.escape(wa, quote=True)}" {a}>{html.escape(S["SHARE_WHATSAPP"])}</a>'
        f'<a style="{item}" href="{html.escape(x, quote=True)}" {a}>{html.escape(S["SHARE_X"])}</a>'
        f'<a style="{item}" href="{html.escape(tg, quote=True)}" {a}>{html.escape(S["SHARE_TELEGRAM"])}</a>'
        f'<button type="button" style="{item}" role="menuitem" data-copy="{html.escape(url, quote=True)}" '
        f'data-copied="{html.escape(S["SHARE_COPIED"], quote=True)}">{html.escape(S["SHARE_COPY"])}</button>'
        '</div></div>'
        "<script>(function(){var w=document.currentScript.previousElementSibling;"
        "var b=w.querySelector('.sharebtn'),p=w.querySelector('.sharepop');"
        "function close(){p.hidden=true;b.setAttribute('aria-expanded','false');}"
        "function open(){p.hidden=false;b.setAttribute('aria-expanded','true');}"
        "b.addEventListener('click',function(e){e.stopPropagation();"
        "if(navigator.share){navigator.share({title:b.getAttribute('data-title'),text:b.getAttribute('data-text'),url:b.getAttribute('data-url')}).catch(function(){});return;}"
        "if(p.hidden)open();else close();});"
        "document.addEventListener('click',function(e){if(!w.contains(e.target))close();});"
        "document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});"
        "var cp=p.querySelector('[data-copy]');"
        "if(cp){cp.addEventListener('click',function(){var u=cp.getAttribute('data-copy');"
        "function done(){var t=cp.getAttribute('data-copied')||'Copied';var o=cp.textContent;"
        "cp.textContent=t;setTimeout(function(){cp.textContent=o;close();},1100);}"
        "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(u).then(done).catch(done);}else{done();}});}"
        "})();</script>"
    )


def _mast_story_link(S: dict, lang: str) -> str:
    """The masthead '▶ Story' link (gated by STORY_SHARE_ENABLED)."""
    href = _page_link("story", lang)
    return (f'<a class="same-tab" href="{href}" style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;'
            'letter-spacing:.12em;text-transform:uppercase;color:#C03A22;font-weight:600;text-decoration:none;'
            'border-bottom:1px solid rgba(192,58,34,.4)"><span aria-hidden="true">&#9654;</span> '
            f'{html.escape(S["STORY_ENTRY"])}</a>')


def _story_share_row(S: dict, lang: str) -> str:
    """The bottom-line 'Open story mode' button + the full share bar (gated by STORY_SHARE_ENABLED)."""
    href = _page_link("story", lang)
    btn = (f'<a class="same-tab" href="{href}" style="display:inline-block;font-family:\'IBM Plex Mono\',monospace;'
           'font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:#EFEBDF;'
           'background:#1A1813;padding:12px 18px;border-radius:3px;text-decoration:none">'
           f'<span aria-hidden="true">&#9654;</span>&nbsp;{html.escape(S["STORY_OPEN"])}</a>')
    return ('<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-top:30px">'
            + btn + _share_bar(S, _LANG_META[lang]["OG_URL"]) + '</div>')


def _money_rows(effects: list[dict], labels: dict) -> str:
    by = {e["stoppage_type"]: e for e in effects}
    out = []
    for stype in _ORDER:
        e = by.get(stype)
        if not e or e["n"] == 0:
            continue
        mean = e["mean_delta"]
        a, b = abs(e["ci_lo"]), abs(e["ci_hi"])
        lo, hi = min(a, b), max(a, b)
        mean_pct = min(abs(mean) / SCALE * 100, 100)
        lo_pct, hi_pct = min(lo / SCALE * 100, 100), min(hi / SCALE * 100, 100)
        is_hl = stype == "hydration"
        color = ACCENT if is_hl else INK
        out.append(f"""
        <div style="position:relative;margin-bottom:18px">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:9px">
            <span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:16px;color:{color}">{labels[stype]}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">n = {e['n']}</span>
          </div>
          <div style="position:relative;height:30px">
            <div style="position:absolute;top:13px;height:4px;right:0;width:{mean_pct:.2f}%;background:{color};opacity:{1 if is_hl else .85}"></div>
            <div style="position:absolute;top:9px;height:12px;right:{lo_pct:.2f}%;width:{hi_pct - lo_pct:.2f}%;border-left:1px solid {color};border-right:1px solid {color};background:{color};opacity:{.16 if is_hl else .12}"></div>
            <div style="position:absolute;top:9px;width:12px;height:12px;border-radius:50%;right:calc({mean_pct:.2f}% - 6px);background:{color};box-shadow:0 0 0 3px #EFEBDF"></div>
            <span style="position:absolute;top:-2px;font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:15px;color:{color};right:calc({mean_pct:.2f}% + 14px)">{mean:.0f}</span>
          </div>
        </div>""")
    return "".join(out)


def _fmt_date_epoch(ts) -> str:
    """Epoch seconds → DD/MM/YYYY (UTC, kickoff date). Locale-neutral, used in both languages."""
    if not ts:
        return ""
    try:
        ts = int(float(ts))
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d/%m/%Y")


def _stage_meta(league: str | None, rnd, stage: dict) -> tuple[str, tuple]:
    """(display label, sort key) for a match's stage. Groups first (A→L), then knockouts in order."""
    league = league or ""
    if "Grp." in league:
        letter = league.split("Grp.")[-1].strip()
        return (stage["group"].format(letter=letter), (0, letter))
    key = rnd.lower() if isinstance(rnd, str) else rnd
    if key in _KO_ORDER:
        return (stage[key], (1, _KO_ORDER[key]))
    return (stage["other"], (2, 0))


def _match_cards(site_figures: Path, F: dict, stage: dict, lang: str) -> str:
    mpath = PROCESSED / "matches.json"
    src_dir = REPORTS / "figures" / "matches"
    pending = f'<p style="font-family:IBM Plex Mono,monospace;color:#5A5547">{F["cards_pending"]}</p>'
    if not mpath.exists() or not src_dir.exists():
        return pending
    matches = json.loads(mpath.read_text(encoding="utf-8"))
    dest = site_figures / "matches"
    dest.mkdir(parents=True, exist_ok=True)

    groups: dict[str, dict] = {}
    idx = 0
    for m in matches:
        png = src_dir / f"{m['id']}.png"
        if not png.exists():
            continue
        idx += 1
        shutil.copyfile(png, dest / f"{m['id']}.png")
        home = html.escape(_team(m.get("home") or UNKNOWN_TEAM, lang))
        away = html.escape(_team(m.get("away") or UNKNOWN_TEAM, lang))
        date = _fmt_date_epoch(m.get("ts"))
        aria = F["open_chart_aria"].format(h=home, a=away)
        card = f"""
          <button type="button" class="mb-card" data-mid="{m['id']}" aria-label="{aria}" style="background:#FCFAF3;border:1px solid #E2DBCA;border-radius:3px;padding:13px 14px 12px;display:flex;flex-direction:column;gap:10px;cursor:pointer;font:inherit;text-align:left;width:100%">
            <span style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><span style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.1em;color:#5A5547">M{idx:02d}{f" · {date}" if date else ""}</span><span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#8A8268">↗</span></span>
            <span style="display:flex;flex-direction:column;gap:4px">
              <span style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:#3E88C7;flex:none"></span><span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:14px;color:#1A1813;line-height:1.15">{home}</span></span>
              <span style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:#E08A4B;flex:none"></span><span style="font-family:'IBM Plex Sans',sans-serif;font-weight:500;font-size:14px;color:#746E5F;line-height:1.15">{away}</span></span>
            </span>
            <img src="figures/matches/{m['id']}.png" alt="" loading="lazy" style="width:100%;height:74px;object-fit:contain;object-position:center;display:block;margin-top:2px"/>
          </button>"""
        label, order = _stage_meta(m.get("league"), m.get("stage"), stage)
        g = groups.setdefault(label, {"order": order, "cards": []})
        g["cards"].append(card)

    if not groups:
        return pending

    out = []
    has_group = has_knockout = False
    for label in sorted(groups, key=lambda lb: groups[lb]["order"]):
        cards = groups[label]["cards"]
        stage_kind = "group" if groups[label]["order"][0] == 0 else "knockout"  # 0=group; else knockout
        has_group = has_group or stage_kind == "group"
        has_knockout = has_knockout or stage_kind == "knockout"
        out.append(
            f'<details class="grp" data-stage="{stage_kind}" open>'
            f'<summary class="grp-h"><span>{label}</span><span class="grp-n">{len(cards)}</span></summary>'
            '<div class="grp-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,210px),1fr));gap:14px">'
            + "".join(cards) + "</div></details>"
        )

    # phase filter tabs (Knockouts only once those matches exist)
    tabs = [f'<button type="button" class="mb-tab on" aria-pressed="true" data-filter="all">{F["tab_all"]}</button>']
    if has_group:
        tabs.append(f'<button type="button" class="mb-tab" aria-pressed="false" data-filter="group">{F["tab_group"]}</button>')
    if has_knockout:
        tabs.append(f'<button type="button" class="mb-tab" aria-pressed="false" data-filter="knockout">{F["tab_knockout"]}</button>')
    tabbar = (f'<div class="mb-tabs" role="group" aria-label="{F["tabs_aria"]}">{"".join(tabs)}</div>'
              if len(tabs) > 1 else "")
    return tabbar + "".join(out)


def _match_names() -> dict[str, tuple[str, str]]:
    """{match_id: (home, away)} from the committed momentum.json."""
    p = PROCESSED / "momentum.json"
    if not p.exists():
        return {}
    return {str(m["id"]): (m.get("home") or UNKNOWN_TEAM, m.get("away") or UNKNOWN_TEAM)
            for m in json.loads(p.read_text(encoding="utf-8"))}


def _extremes_block(df: pl.DataFrame, names: dict[str, tuple[str, str]], F: dict, lang: str) -> str:
    """Descriptive: matches with the biggest / quietest leader momentum swing around a hydration break.

    Match-level only, with the pre-break level shown so the regression-to-the-mean story is visible
    (the bigger the drop, the higher the team was riding). No team ranking — too few breaks each.
    """
    if df is None or df.is_empty():
        return ""
    hyd = df.filter((pl.col("stoppage_type") == "hydration") & (pl.col("momentum_pre_5min_mean") > 0))
    if hyd.is_empty():
        return ""
    per = (hyd.sort("momentum_delta")  # ascending: biggest drop first within each match
           .group_by("match_id", maintain_order=True).first()
           .select("match_id", "team", "momentum_pre_5min_mean", "momentum_delta", "clock_minute")
           .sort("momentum_delta"))
    recs = per.to_dicts()
    if len(recs) < 10:  # need 10 for two disjoint 5-row columns (else biggest/quietest overlap)
        return ""
    biggest, quietest = recs[:5], list(reversed(recs[-5:]))
    vs, frm = F["extremes_vs"], F["extremes_from"]

    def row(r: dict) -> str:
        mid = str(r["match_id"]); h, a = names.get(mid, (UNKNOWN_TEAM, UNKNOWN_TEAM))
        h, a = html.escape(_team(h, lang)), html.escape(_team(a, lang))
        team = html.escape(_team(r["team"], lang))
        drop = r["momentum_delta"]; sign = "−" if drop < 0 else "+"
        aria = F["open_chart_aria"].format(h=h, a=a)
        return (f'<button type="button" class="mb-card" data-mid="{mid}" '
                f'aria-label="{aria}" style="cursor:pointer;display:flex;width:100%;font:inherit;text-align:left;background:none;border:none;'
                f'justify-content:space-between;align-items:baseline;gap:12px;padding:9px 0;border-bottom:1px solid #E6E0CF">'
                # full team names (allowed to wrap); the shared grid keeps the two columns row-aligned
                f'<span style="font-family:\'IBM Plex Sans\',sans-serif;font-size:14px;color:#1A1813;flex:1 1 auto;min-width:0">{h} {vs} {a}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:#1A1813;white-space:nowrap;flex:0 0 auto">'
                f'{team} {sign}{abs(drop):.0f} '
                f'<span style="color:#5A5547">{frm} +{r["momentum_pre_5min_mean"]:.0f} · {int(r["clock_minute"])}\'</span></span></button>')

    hbase = ("font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;"
             "text-transform:uppercase;font-weight:600;margin-bottom:6px;white-space:nowrap")
    hb = f'<div style="{hbase};color:#E5482E">{F["extremes_biggest"]}</div>'
    hq = f'<div style="{hbase};color:#5A5547">{F["extremes_quietest"]}</div>'
    # column-major DOM order (header+5 biggest, then header+5 quietest); CSS .extremes-grid lays them
    # into 6 shared rows so the columns line up, and stacks to one column on mobile.
    body = hb + "".join(row(r) for r in biggest) + hq + "".join(row(r) for r in quietest)
    return f"""
      <div style="margin:4px 0 32px">
        <div class="extremes-grid">{body}</div>
        <p style="font-family:'Newsreader',serif;font-size:17px;line-height:1.55;color:#5A5547;margin-top:20px;max-width:64ch">{F["extremes_note"]}</p>
      </div>"""


def _compare_sentence(effects: list[dict], F: dict) -> str:
    by = {e["stoppage_type"]: abs(e["mean_delta"]) for e in effects if e["n"]}
    hyd = by.get("hydration")
    var = by.get("var")
    inh = by.get("injury_no_huddle")
    hyd_n = next((e["n"] for e in effects if e["stoppage_type"] == "hydration"), 0)
    if not hyd:
        return F["compare_not_enough"]
    bits = []
    if var:
        bits.append(F["compare_pct"].format(pct=round((hyd / var - 1) * 100)))
    if inh:
        bits.append(F["compare_ratio"].format(ratio=f"{hyd / inh:.1f}"))
    comp = F["compare_and"].join(bits) if bits else F["compare_default"]
    return F["compare_sentence"].format(comp=comp, n=hyd_n)


def _match_explanation(df: pl.DataFrame, mid: str, home: str, away: str, F: dict, types: dict) -> str:
    """Short, purely descriptive note on this match's momentum (no causal claims).

    Returns HTML (rendered via innerHTML): minute/momentum values are wrapped in styled spans by
    the exp_* templates, so team names are escaped here.
    """
    home, away = html.escape(home), html.escape(away)
    if df is None or df.is_empty():
        return F["exp_no_df"].format(home=home, away=away)
    rows = (df.filter((pl.col("match_id") == str(mid)) & (pl.col("is_home") == True))  # noqa: E712
            .sort("clock_minute").to_dicts())
    if not rows:
        return F["exp_no_stop"].format(home=home, away=away)
    parts: list[str] = []
    for r in rows:
        if r["stoppage_type"] != "hydration":
            continue
        pre, d = r.get("momentum_pre_5min_mean"), r.get("momentum_delta")
        if pre is None or d is None:
            continue
        leader = home if pre > 0 else away
        lead_delta = d if pre > 0 else -d  # change over the 5 min after, from the leader's perspective
        m = int(r["clock_minute"])
        # Grade the lead clause to how big the pre-break edge actually was. The text reads the 5-min
        # average *before* the break, which can be a faint, fading edge (e.g. a bottom-decile +4.6) —
        # calling that "dominating" misreads the chart. Thresholds from the |pre| distribution
        # (p10~5, p50~25, p75~42): under 8 = roughly even, 40+ = clearly on top.
        a = abs(pre)
        tier = "exp_lead_marginal" if a < 8 else ("exp_lead_strong" if a >= 40 else "exp_lead_moderate")
        lead = F[tier].format(leader=leader)
        x = f"{abs(lead_delta):.0f}"
        key = "exp_held" if x == "0" else ("exp_lost" if lead_delta < 0 else "exp_pushed")
        parts.append(F[key].format(m=m, lead=lead, x=x))
    sw = max(rows, key=lambda r: abs(r.get("momentum_delta") or 0))
    if sw.get("momentum_delta") is not None:
        st = sw["stoppage_type"]
        parts.append(F["exp_swing"].format(x=f"{abs(sw['momentum_delta']):.0f}",
                                            m=int(sw["clock_minute"]),
                                            type=types.get(st, st.replace("_", " "))))
    return " ".join(parts) or F["exp_fallback"].format(home=home, away=away)


def _mb_data(df: pl.DataFrame, F: dict, types: dict, lang: str) -> str:
    """Augment committed momentum.json with a per-match explanation; return JSON for the modal.

    Team names are localized for `lang` here so the modal title, share card, SVG aria-label and the
    `explain` text all read in the page's language (the JS reads names straight from this blob).
    """
    p = PROCESSED / "momentum.json"
    if not p.exists():
        return "[]"
    data = json.loads(p.read_text(encoding="utf-8"))
    for m in data:
        home = _team(m.get("home") or UNKNOWN_TEAM, lang)
        away = _team(m.get("away") or UNKNOWN_TEAM, lang)
        m["home"], m["away"] = home, away
        m["explain"] = _match_explanation(df, m["id"], home, away, F, types)
    return json.dumps(data, ensure_ascii=False)


def _load_twfe():
    """The committed signed-off TWFE momentum-killer estimate, or None if absent/gated/unavailable.

    Computed locally (statsmodels) by `pipeline.build_twfe` and persisted to data/processed/twfe.json,
    so the statsmodels-free CI build can report it without re-fitting.
    """
    p = PROCESSED / "twfe.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not d.get("available") or d.get("gated") or "coef" not in d:
        return None
    return d


def _placebo_meanci(parquet_name: str):
    """(mean, lo, hi, n, matches) for an on-top FotMob placebo parquet, or None if absent/empty."""
    p = PROCESSED / parquet_name
    if not p.exists():
        return None
    top = on_top_rows(pl.read_parquet(p))
    if top.is_empty():
        return None
    mean, lo, hi = cluster_bootstrap_ci(top)
    return (mean, lo, hi, top.height, top["match_id"].n_unique())


def _info(tip: str, aria: str) -> str:
    """A small accessible info-tooltip trigger (ⓘ). `tip`/`aria` are plain text (no double quotes)."""
    return f'<button type="button" class="info" aria-label="{aria}" data-tip="{tip}">i</button>'


def _compare_chart(effects: list[dict], F: dict) -> str:
    """Dot-and-whisker comparison: the 2026 break drop vs no-break baselines, same FotMob scale."""
    aria = F["info_aria"]
    rows_data = []
    hyd = {e["stoppage_type"]: e for e in effects}.get("hydration")
    if hyd and hyd.get("n"):
        rows_data.append((F["cc_hyd_label"], F["cc_hyd_sub"],
                          hyd["mean_delta"], hyd["ci_lo"], hyd["ci_hi"], hyd["n"], hyd.get("n_matches"), ACCENT, True, F["tip_read"]))
    NT = "#5A5547"      # national-team no-break baselines
    CLUBS = "#9A6A3A"   # club football, the contrast
    p26 = _placebo_meanci("placebo2026.parquet")
    if p26:  # the same WC2026 teams at quiet minutes — the gold-standard control
        rows_data.append((F["cc_p26_label"], F["cc_p26_sub"],
                          p26[0], p26[1], p26[2], p26[3], p26[4], ACCENT, False, F["tip_placebo"]))
    # All baselines below are NO-BREAK controls -> hollow dot (solid=False), so the encoding is
    # consistent: only the mandated break (hydration, above) gets a filled dot. Colour carries the
    # group: accent = same 2026 teams, grey = other national teams, brown = club football.
    euro = _placebo_meanci("euro2024_placebo.parquet")
    if euro:
        rows_data.append((F["cc_euro_label"], F["cc_euro_sub"],
                          euro[0], euro[1], euro[2], euro[3], euro[4], NT, False, None))
    copa = _placebo_meanci("copa2024_placebo.parquet")
    if copa:
        rows_data.append((F["cc_copa_label"], F["cc_copa_sub"],
                          copa[0], copa[1], copa[2], copa[3], copa[4], NT, False, F["tip_copa"]))
    w22 = _placebo_meanci("wc2022_placebo.parquet")
    if w22:
        rows_data.append((F["cc_wc22_label"], F["cc_wc22_sub"],
                          w22[0], w22[1], w22[2], w22[3], w22[4], NT, False, None))
    cwc = _placebo_meanci("cwc2025_placebo.parquet")
    if cwc:  # clubs regress more — the contrast that used to flatter the "same drop" story
        rows_data.append((F["cc_cwc_label"], F["cc_cwc_sub"],
                          cwc[0], cwc[1], cwc[2], cwc[3], cwc[4], CLUBS, False, None))

    out = []
    for label, sub, mean, lo, hi, n, matches, color, solid, tip in rows_data:
        a, b = abs(lo), abs(hi)
        losp, hisp = min(min(a, b) / SCALE * 100, 100), min(max(a, b) / SCALE * 100, 100)
        mp = min(abs(mean) / SCALE * 100, 100)
        dot_fill = color if solid else "#EFEBDF"
        n_lbl = f"n = {n}" + (F["cc_matches"].format(m=matches) if matches else "")
        out.append(f"""
        <div style="position:relative;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px">
            <span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15.5px;color:{color}">{label}{_info(tip, aria) if tip else ""}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#6B6557">{n_lbl}</span>
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.02em;color:#5A5547;margin-bottom:8px">{sub}</div>
          <div style="position:relative;height:26px">
            <div style="position:absolute;top:11px;height:4px;right:0;width:{mp:.2f}%;background:{color};opacity:{.9 if solid else .35}"></div>
            <div style="position:absolute;top:7px;height:12px;right:{losp:.2f}%;width:{hisp - losp:.2f}%;background:{color};opacity:.13"></div>
            <div style="position:absolute;top:7px;width:12px;height:12px;border-radius:50%;right:calc({mp:.2f}% - 6px);background:{dot_fill};border:2px solid {color};box-shadow:0 0 0 3px #EFEBDF"></div>
            <span style="position:absolute;top:-4px;font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:14px;color:{color};right:calc({mp:.2f}% + 14px)">{mean:.0f}</span>
          </div>
        </div>""")
    if not out:
        return ""
    axis = ('<div style="display:flex;justify-content:space-between;font-family:\'IBM Plex Mono\',monospace;'
            'font-size:10.5px;color:#5A5547;margin-top:2px"><span>−30</span><span>−20</span><span>−10</span><span>0</span></div>'
            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#6B6557;margin-top:3px">{F["cc_axis_dir"]}</div>')

    def _sw(html: str) -> str:  # one legend swatch + label
        return f'<span style="display:inline-flex;align-items:center;gap:6px">{html}</span>'

    legend = (
        '<div style="display:flex;gap:14px 18px;flex-wrap:wrap;align-items:center;'
        'font-family:\'IBM Plex Mono\',monospace;font-size:10.5px;color:#5A5547;margin:0 0 18px">'
        + _sw(f'<span style="width:11px;height:11px;border-radius:50%;background:{ACCENT};border:2px solid {ACCENT}"></span>{F["cc_leg_break"]}')
        + _sw(f'<span style="width:11px;height:11px;border-radius:50%;background:#EFEBDF;border:2px solid #5A5547"></span>{F["cc_leg_ctrl"]}')
        + _sw(f'<span style="width:12px;height:4px;background:{ACCENT}"></span>{F["cc_leg_2026"]}')
        + _sw(f'<span style="width:12px;height:4px;background:{NT}"></span>{F["cc_leg_nt"]}')
        + _sw(f'<span style="width:12px;height:4px;background:{CLUBS}"></span>{F["cc_leg_club"]}')
        + '</div>'
    )
    return '<div style="margin:26px 0 8px">' + legend + "".join(out) + axis + "</div>"


def _heat_tokens(df: pl.DataFrame) -> dict[str, str]:
    """Per-match heat distribution for the 'did they need them?' note (numeric, language-neutral)."""
    m = (df.group_by("match_id").agg(pl.col("wbgt").first(), pl.col("dome").first())
         .drop_nulls("wbgt"))
    if m.is_empty():
        return {"HEAT_N": "0", "HEAT_HOT32": "0", "HEAT_HOT28": "0", "HEAT_DOMED": "0", "HEAT_MEDIAN": "—"}
    return {
        "HEAT_N": str(m.height),
        "HEAT_HOT32": str(m.filter(pl.col("wbgt") >= 32).height),
        "HEAT_HOT28": str(m.filter(pl.col("wbgt") >= 28).height),
        "HEAT_DOMED": str(m.filter(pl.col("dome") == True).height),  # noqa: E712
        "HEAT_MEDIAN": f"{m['wbgt'].median():.0f}",
    }


# §06 heat stat grid. Inner {{HEAT_*}} tokens resolve in the multi-pass; "" when there's no WBGT data
# (so the page never shows a "0/0" / "—°" empty grid).
_HEAT_GRID_HTML = (
    '<div style="display:flex;gap:30px;flex-wrap:wrap;border-top:2px solid #1A1813;border-bottom:1px solid #DDD6C5;padding:26px 0;margin-bottom:26px">'
    '<div style="flex:1 1 150px"><div style="font-family:\'Newsreader\',serif;font-size:44px;font-weight:500;color:#E5482E;line-height:1">{{HEAT_HOT32}}/{{HEAT_N}}</div><div style="font-family:\'IBM Plex Sans\',sans-serif;font-size:13.5px;color:#46412F;margin-top:8px;line-height:1.45">{{HEAT_DESC32}}</div></div>'
    '<div style="flex:1 1 150px"><div style="font-family:\'Newsreader\',serif;font-size:44px;font-weight:500;color:#1A1813;line-height:1">{{HEAT_DOMED}}</div><div style="font-family:\'IBM Plex Sans\',sans-serif;font-size:13.5px;color:#46412F;margin-top:8px;line-height:1.45">{{HEAT_DESC_DOME}}</div></div>'
    '<div style="flex:1 1 150px"><div style="font-family:\'Newsreader\',serif;font-size:44px;font-weight:500;color:#1A1813;line-height:1">{{HEAT_MEDIAN}}°</div><div style="font-family:\'IBM Plex Sans\',sans-serif;font-size:13.5px;color:#46412F;margin-top:8px;line-height:1.45">{{HEAT_DESC_MEDIAN}}</div></div>'
    '</div>'
)


def _heat_grid(has_data: bool) -> str:
    return _HEAT_GRID_HTML if has_data else ""


def _altitude_count(df: pl.DataFrame, threshold_m: int = 1500) -> int:
    """Number of matches whose venue sits at/above `threshold_m` (Mexico City, Guadalajara)."""
    if df is None or df.is_empty() or "venue" not in df.columns:
        return 0
    mv = df.group_by("match_id").agg(pl.col("venue").first()).drop_nulls("venue")
    return sum(1 for v in mv["venue"].to_list() if (venue_elev_m(v) or 0) >= threshold_m)


def _accl_tokens(parquet_name: str = "acclimatization.parquet") -> dict[str, str]:
    """Tokens for the methodology heat section, from the committed acclimatization parquet.

    Per-tournament heat gap + drop, the within-group gap→drop slopes (+CIs), and a couple of
    counts. All "—" if the parquet is absent (the method page then shows a 'pending' note).
    """
    keys = ["ACCL_WC26_GAP", "ACCL_WC26_DROP", "ACCL_COPA_GAP", "ACCL_COPA_DROP",
            "ACCL_EURO_GAP", "ACCL_EURO_DROP", "ACCL_CWC_GAP", "ACCL_CWC_DROP",
            "ACCL_SLOPE_CWC", "ACCL_CWC_LO", "ACCL_CWC_HI",
            "ACCL_SLOPE_NAT", "ACCL_NAT_LO", "ACCL_NAT_HI",
            "ACCL_GAP_MAX", "ACCL_N", "ACCL_CLUBS"]
    blank = dict.fromkeys(keys, "—")
    p = PROCESSED / parquet_name
    if not p.exists():
        return blank
    from src.analysis.acclimatization import summarize_acclimatization

    res = summarize_acclimatization(pl.read_parquet(p), n_boot=800)
    pt = res.get("per_tournament", {})
    out = dict(blank)
    for tour, tok in (("WC2026", "WC26"), ("Copa2024", "COPA"), ("Euro2024", "EURO"), ("CWC2025", "CWC")):
        v = pt.get(tour)
        if v:
            out[f"ACCL_{tok}_GAP"] = f"{v['gap_mean']:+.0f}"
            out[f"ACCL_{tok}_DROP"] = f"{v['drop_mean']:+.0f}"

    def _slope(test_key, lo_tok, hi_tok, slope_tok):
        r = res.get(test_key, {})
        s = r.get("slope_per_C")
        if s and s["slope"] == s["slope"]:  # not NaN
            out[slope_tok] = f"{s['slope']:+.2f}"
            out[lo_tok] = f"{s['ci_lo']:+.2f}"
            out[hi_tok] = f"{s['ci_hi']:+.2f}"

    _slope("cwc_clubs_test", "ACCL_CWC_LO", "ACCL_CWC_HI", "ACCL_SLOPE_CWC")
    _slope("nations_test", "ACCL_NAT_LO", "ACCL_NAT_HI", "ACCL_SLOPE_NAT")
    gaps = [v["gap_mean"] for v in pt.values()]
    if gaps:
        out["ACCL_GAP_MAX"] = f"{max(gaps):.0f}"
    n_rows = sum(v["n"] for v in pt.values()) if pt else 0
    out["ACCL_N"] = str(n_rows) if n_rows else "—"
    # Clubs-placed count: prefer the committed meta (written by build_acclimatization) so the CI
    # site build — which has no gitignored raw/fotmob_clubs dir — renders the real number, not "—".
    meta = PROCESSED / "accl_meta.json"
    if meta.exists():
        try:
            out["ACCL_CLUBS"] = str(json.loads(meta.read_text(encoding="utf-8")).get("clubs_placed", "—"))
        except Exception:
            out["ACCL_CLUBS"] = "—"
    else:
        clubs_dir = RAW / "fotmob_clubs"
        out["ACCL_CLUBS"] = str(len(list(clubs_dir.glob("*.json")))) if clubs_dir.exists() else "—"
    return out


def _fmt_mmss(sec: int) -> str:
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def _duration_tokens(df: pl.DataFrame) -> dict[str, str]:
    """Measured hydration-break durations + the longer-breaks-bite-harder split (from ESPN delays)."""
    keys = ["DUR_MEDIAN", "DUR_MIN", "DUR_MAX", "DUR_N", "DUR_N_ALL", "DUR_SHORT", "DUR_LONG", "DUR_SLOPE"]
    out = dict.fromkeys(keys, "—")
    from src.analysis.duration_effect import duration_effect, duration_summary

    s = duration_summary(df)
    if not s.get("n"):
        return out
    out.update({"DUR_MEDIAN": _fmt_mmss(s["median"]), "DUR_MIN": _fmt_mmss(s["min"]),
                "DUR_MAX": _fmt_mmss(s["max"]), "DUR_N": str(s["n"]), "DUR_N_ALL": str(s["n_all"])})
    e = duration_effect(df, n_boot=800)
    if "slope_per_min" in e:
        out["DUR_SHORT"] = str(round(abs(e["short"]["mean"])))
        out["DUR_LONG"] = str(round(abs(e["long"]["mean"])))
        out["DUR_SLOPE"] = str(round(abs(e["slope_per_min"]["slope"])))
    return out


def _breaks_per_team(df: pl.DataFrame) -> tuple[str, str]:
    """(min, max) on-top hydration breaks any single team has had so far (for the extremes note)."""
    if df is None or df.is_empty():
        return ("—", "—")
    ot = on_top_rows(df).filter(pl.col("stoppage_type") == "hydration")
    if ot.is_empty():
        return ("—", "—")
    counts = ot.group_by("team").agg(pl.len().alias("n"))["n"]
    return (str(int(counts.min())), str(int(counts.max())))


def _trend_section(snapshots: list[dict], hyd_mean: float | None, hyd_n: int, updated: str, F: dict) -> str:
    est = f"−{abs(hyd_mean):.0f}" if hyd_mean is not None else "—"  # integer, matches the −25 headline
    body = F["trend_sentence"].format(updated=updated, est=est, n=hyd_n)
    return f"""
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6">
    <div style="max-width:840px;margin:0 auto;padding:46px 40px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:16px">{F["trend_label"]}</div>
      <p style="font-family:'Newsreader',serif;font-size:20px;line-height:1.6;color:#2B2820;max-width:60ch">{body}</p>
    </div>
  </section>"""


def finding_signature() -> dict:
    """The headline numbers the committed social artifacts (og.png, story stills, story.mp4) depend
    on — recomputed from the committed parquet exactly as build() computes them. refresh_social()
    compares this against reports/figures/render_state.json so the binaries are only re-rendered when
    the underlying data actually moves (no daily churn when no new matches landed)."""
    if not STOPPAGES_PARQUET.exists():
        return {}
    df = load_processed()
    if df.is_empty():
        return {}
    by = {e["stoppage_type"]: e for e in effect_by_type(df)}
    hyd = by.get("hydration", {})
    p26 = _placebo_meanci("placebo2026.parquet")
    from src.analysis.descriptive import gap_adjusted_ci
    _ppath = PROCESSED / "placebo2026.parquet"
    _g = gap_adjusted_ci(df, pl.read_parquet(_ppath)) if _ppath.exists() else None
    snaps = load_all_snapshots()
    sig = {
        "hero": round(abs(hyd["mean_delta"])) if hyd and hyd.get("n") else None,
        "p26": round(abs(p26[0])) if p26 else None,
        "n_matches": int(df["match_id"].n_unique()),
        "snap": snaps[-1]["date"] if snaps else None,
    }
    if _g:
        sig["gap"] = round(abs(_g["gap"]))
        sig["gap_lo"] = round(-_g["hi"])
        sig["gap_hi"] = round(-_g["lo"])
        sig["gap_excl0"] = bool(_g["hi"] < 0 or _g["lo"] > 0)
    return sig


def build() -> str:
    SITE.mkdir(parents=True, exist_ok=True)
    site_figures = SITE / "figures"
    site_figures.mkdir(parents=True, exist_ok=True)
    # social/share assets + the committed methodology PDFs live at the site root (generated
    # locally — CI has no browser — and copied in on every build, like og.png).
    for icon in ("og.png", "og.es.png", "apple-touch-icon.png",
                 "wc2026-methodology.pdf", "wc2026-methodology.es.pdf",
                 "story.mp4", "story.es.mp4", "reel.mp4", "reel.es.mp4"):
        src = REPORTS / "figures" / icon
        if src.exists():
            shutil.copyfile(src, SITE / icon)
    # story-mode still PNGs (1080x1920, generated locally via --story-cards, committed) → site/story/
    story_src = REPORTS / "figures" / "story"
    if story_src.exists():
        for png in story_src.rglob("*.png"):
            dest = SITE / "story" / png.relative_to(story_src)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(png, dest)

    if not STOPPAGES_PARQUET.exists() or load_processed().is_empty():
        first_out = None
        for lang in LANGS:  # write both siblings so the toggle/hreflang never dangle
            other = _OUTFILE["es" if lang == "en" else "en"]
            other_label = "Español" if lang == "en" else "English"
            out = SITE / _OUTFILE[lang]
            out.write_text(f"<!doctype html><html lang='{lang}'><meta charset=utf-8>"
                           "<title>WC2026 Momentum</title>"
                           "<body style='font-family:sans-serif;max-width:640px;margin:60px auto'>"
                           "<h1>WC2026 — Stoppage Momentum</h1>"
                           "<p>No data yet. Check back after the next match.</p>"
                           f"<p><a href='{other}'>{other_label}</a></p>", encoding="utf-8")
            first_out = first_out or str(out)
        return first_out

    df = load_processed()
    effects = effect_by_type(df)
    by = {e["stoppage_type"]: e for e in effects}
    hyd = by.get("hydration", {})
    snapshots = load_all_snapshots()
    snap_date = snapshots[-1]["date"] if snapshots else None
    names = _match_names()

    def mech(stype: str) -> str:
        e = by.get(stype)
        return f"{e['mean_delta']:.0f}" if e and e["n"] else "—"

    # No-break placebo figures, computed once and tokenized so prose can't drift from the data.
    def _absround(x) -> str:
        return str(round(abs(x))) if x is not None else "—"

    p26 = _placebo_meanci("placebo2026.parquet")
    cwc = _placebo_meanci("cwc2025_placebo.parquet")
    w22 = _placebo_meanci("wc2022_placebo.parquet")
    copa = _placebo_meanci("copa2024_placebo.parquet")
    euro = _placebo_meanci("euro2024_placebo.parquet")
    # National-team no-break baselines (NOT clubs) for the range cited in §05.
    nt = sorted(round(abs(x[0])) for x in (p26, euro, copa, w22) if x)
    hero = round(abs(hyd["mean_delta"])) if hyd and hyd.get("n") else None
    p26r = round(abs(p26[0])) if p26 else None
    # Level-adjusted break-vs-no-break gap (nets out regression to the mean) with a match-clustered
    # bootstrap CI — numpy-only, from the committed stoppages + placebo2026 parquets, so it recomputes
    # identically in CI. Replaces the old round(|hero|)-round(|p26|) difference, which had no interval.
    from src.analysis.descriptive import gap_adjusted_ci
    _ppath = PROCESSED / "placebo2026.parquet"
    _g = gap_adjusted_ci(df, pl.read_parquet(_ppath)) if _ppath.exists() else None
    if _g:
        gap = round(abs(_g["gap"]))
        gap_lo, gap_hi = -_g["hi"], -_g["lo"]          # extra-drop framing (positive = break bites harder)
        gap_excl0 = _g["hi"] < 0 or _g["lo"] > 0        # does the difference's 95% CI clear zero?
    else:
        gap, gap_lo, gap_hi, gap_excl0 = None, None, None, False
    twfe = _load_twfe()
    # calibrated, data-driven verdict clauses (resolved per-language in both the index and method builds):
    # the gap copy firms up automatically if/when the difference CI ever clears zero; the TWFE clause
    # reports the actual (currently null) signed-off model.
    gap_clause_key = "GAP_CLAUSE_SIG" if gap_excl0 else "GAP_CLAUSE_OPEN"
    twfe_clause_key = ("TWFE_CLAUSE_SIG" if (twfe and twfe["pvalue"] < 0.05)
                       else "TWFE_CLAUSE_NULL" if twfe else "TWFE_CLAUSE_HELD")
    r2 = pre_level_r2(df)
    heat = _heat_tokens(df)
    breaks_min, breaks_max = _breaks_per_team(df)
    data_tokens = {
        **heat,
        "HEAT_GRID": _heat_grid(heat["HEAT_N"] != "0"),
        "HEAT_ALT": str(_altitude_count(df)),
        "HERO_DELTA": _absround(hyd.get("mean_delta")) if hyd else "—",
        "P26_DELTA": _absround(p26[0] if p26 else None),
        "CWC_DELTA": _absround(cwc[0] if cwc else None),
        "WC22_DELTA": _absround(w22[0] if w22 else None),
        "COPA_DELTA": _absround(copa[0] if copa else None),
        "EURO_DELTA": _absround(euro[0] if euro else None),
        "NOBREAK_LO": str(nt[0]) if nt else "—",
        "NOBREAK_HI": str(nt[-1]) if nt else "—",
        "GAP": str(gap) if gap is not None else "—",
        "GAP_LO": f"{gap_lo:+.0f}" if gap_lo is not None else "—",
        "GAP_HI": f"{gap_hi:+.0f}" if gap_hi is not None else "—",
        "TWFE_COEF": f"{twfe['coef']:+.2f}" if twfe else "—",
        "TWFE_CI": f"{twfe['ci_lo']:+.2f} to {twfe['ci_hi']:+.2f}" if twfe else "—",
        "TWFE_P": f"{twfe['pvalue']:.2f}" if twfe else "—",
        "TWFE_N": str(twfe["n_obs"]) if twfe else "—",
        "GAP_CLAUSE_KEY": gap_clause_key,
        "TWFE_CLAUSE_KEY": twfe_clause_key,
        "BREAKS_MIN": breaks_min,
        "BREAKS_MAX": breaks_max,
        "PRE_R2": str(round(r2 * 100)) if r2 is not None else "—",
        "HYD_N": str(hyd.get("n", 0)),
        "N_MATCHES": str(df["match_id"].n_unique()),
        "N_STOPPAGES": str(df["stoppage_id"].n_unique()),
        "COPA_N": str(copa[3]) if copa else "—",  # on-top windows behind the Copa baseline (for the tooltip)
        **_accl_tokens(),
        **_duration_tokens(df),
    }

    first_out = None
    for lang in LANGS:
        S = STRINGS[lang]
        F = FRAG[lang]
        updated = _fmt_date_iso(snap_date, lang)
        tokens = {
            **S,
            **_LANG_META[lang],
            **data_tokens,
            "GAP_CLAUSE": S[gap_clause_key],
            "TWFE_CLAUSE": S[twfe_clause_key],
            "BOTTOM_LEAD": S["BOTTOM_LEAD_SIG" if gap_excl0 else "BOTTOM_LEAD_OPEN"],
            "UPDATED_DATE": updated.upper(),
            "N_MATCHES": str(df["match_id"].n_unique()),
            "N_STOPPAGES": str(df["stoppage_id"].n_unique()),
            "HYD_N": str(hyd.get("n", 0)),
            "MONEY_ROWS": _money_rows(effects, LABELS[lang]),
            "COMPARE_SENTENCE": _compare_sentence(effects, F),
            "COMPARE_CHART": _compare_chart(effects, F),
            "EXTREMES": _extremes_block(df, names, F, lang),
            "MATCH_CARDS": _match_cards(site_figures, F, STAGE[lang], lang),
            "MECH_HYD": mech("hydration"), "MECH_VAR": mech("var"),
            "MECH_IH": mech("injury_huddle"), "MECH_INH": mech("injury_no_huddle"),
            "TREND": _trend_section(snapshots, hyd.get("mean_delta"), hyd.get("n", 0), updated, F),
            "PAGES_URL": PAGES_URL,
            "METHOD_HREF": _page_link("method", lang),
            # Story-mode + share entry points — temporarily hidden via STORY_SHARE_ENABLED (the pages
            # and helpers stay intact; flip the flag to restore). See project memory.
            "MAST_STORY": _mast_story_link(S, lang) if STORY_SHARE_ENABLED else "",
            "STORY_SHARE_ROW": _story_share_row(S, lang) if STORY_SHARE_ENABLED else "",
            "SHARE_BTN": _share_button(S, _LANG_META[lang]["OG_URL"]) if STORY_SHARE_ENABLED else "",
            "LANG_TOGGLE": _lang_toggle(lang),
            "SNAPSHOT_DATE": snap_date or updated,
            "SNAPSHOT_ISO": snap_date or "",
            # escape "</" so a stray "</script>" inside any team name / string can't close the
            # inline <script> early (standard safe-JSON-in-HTML practice; "<\/" parses back to "</")
            "JS_STRINGS": json.dumps(JS[lang], ensure_ascii=False).replace("</", "<\\/"),
            "MB_DATA": _mb_data(df, F, TYPES[lang], lang).replace("</", "<\\/"),
        }

        page = TEMPLATE
        for _ in range(6):  # iterate to a fixed point so tokens nested in prose values resolve
            before = page
            for k, v in tokens.items():
                page = page.replace("{{" + k + "}}", str(v))
            if page == before:
                break
        leftover = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", page)))
        if leftover:
            raise ValueError(f"unresolved template tokens in {lang} build: {leftover}")
        out = SITE / _OUTFILE[lang]
        out.write_text(page, encoding="utf-8")
        if first_out is None:
            first_out = str(out)

    build_method_pages(data_tokens, snap_date)
    build_story_pages(data_tokens, snap_date)
    build_reel_pages(data_tokens, snap_date)
    return first_out or str(SITE / "index.html")


def build_method_pages(data_tokens: dict, snap_date: str | None) -> None:
    """Render the bilingual methodology / full-report pages (method.html + method.es.html).

    Mirrors the index build loop: prose from STRINGS[lang] (METHOD_* keys) + shared data tokens
    (deltas, acclimatization), same multi-pass + leak guard. Prose-only template, no JS/modal.
    """
    from src.report.method_copy import TEMPLATE as METHOD_TEMPLATE

    for lang in LANGS:
        S = STRINGS[lang]
        updated = _fmt_date_iso(snap_date, lang)
        tokens = {
            **S,
            **data_tokens,
            "LANG": lang,
            "METHOD_CANONICAL": SITE_BASE + _page_link("method", lang),
            "HOME_HREF": _page_link("index", lang),
            "METHOD_HREF": _page_link("method", lang),
            "METHOD_PDF_HREF": "wc2026-methodology.pdf" if lang == "en" else "wc2026-methodology.es.pdf",
            "GAP_CLAUSE": S[data_tokens["GAP_CLAUSE_KEY"]],
            "TWFE_CLAUSE": S[data_tokens["TWFE_CLAUSE_KEY"]],
            "UPDATED_DATE": updated.upper(),
            "LANG_TOGGLE": _lang_toggle(lang, "method"),
            "PAGES_URL": PAGES_URL,
        }
        page = METHOD_TEMPLATE
        for _ in range(6):
            before = page
            for k, v in tokens.items():
                page = page.replace("{{" + k + "}}", str(v))
            if page == before:
                break
        leftover = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", page)))
        if leftover:
            raise ValueError(f"unresolved method tokens in {lang} build: {leftover}")
        (SITE / _page_link("method", lang)).write_text(page, encoding="utf-8")


def build_story_pages(data_tokens: dict, snap_date: str | None) -> None:
    """Render the bilingual 9:16 story-mode pages (story.html + story.es.html).

    Mirrors build_method_pages: prose from STRINGS[lang] (STORY_*/SHARE_* keys) + the shared data
    tokens (HERO_DELTA, P26_DELTA, GAP, GAP_CLAUSE, N_MATCHES…), same multi-pass + leak guard.
    Pure-Python → runs in CI; the animated page needs no browser. The 1080x1920 still PNGs are a
    separate, local-only Playwright step (src/viz/social.build_story_cards via `--story-cards`)."""
    from src.report.story_copy import TEMPLATE as STORY_TEMPLATE

    for lang in LANGS:
        S = STRINGS[lang]
        story_file = _page_link("story", lang)
        other = "story.es.html" if lang == "en" else "story.html"
        other_label = "Español" if lang == "en" else "English"
        story_lang = (f'<a class="cbtn no-nav same-tab" href="{other}">{other_label}</a>')
        tokens = {
            **S,
            **data_tokens,
            **_LANG_META[lang],            # LANG, OG_IMAGE, OG_URL …
            "STORY_CANONICAL": SITE_BASE + story_file,
            "HOME_HREF": _page_link("index", lang),
            "STORY_DIR": lang,
            "STORY_VID": "story.mp4" if lang == "en" else "story.es.mp4",
            "STORY_REEL_VID": "reel.mp4" if lang == "en" else "reel.es.mp4",
            "STORY_LANG": story_lang,
            "SHARE_BAR": _share_bar(S, SITE_BASE + story_file),
            "GAP_CLAUSE": S[data_tokens["GAP_CLAUSE_KEY"]],
            "TWFE_CLAUSE": S[data_tokens["TWFE_CLAUSE_KEY"]],
        }
        page = STORY_TEMPLATE
        for _ in range(6):
            before = page
            for k, v in tokens.items():
                page = page.replace("{{" + k + "}}", str(v))
            if page == before:
                break
        leftover = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", page)))
        if leftover:
            raise ValueError(f"unresolved story tokens in {lang} build: {leftover}")
        (SITE / story_file).write_text(page, encoding="utf-8")


def build_reel_pages(data_tokens: dict, snap_date: str | None) -> None:
    """Render the bilingual ~15s kinetic reel pages (reel.html + reel.es.html).

    Same per-lang token fill + leak guard as build_story_pages; this page auto-plays a fast timeline
    and exists to be recorded into a Reel/TikTok (src/viz/social.build_reel_video). The short verdict
    clause is CI-templated from the same GAP_CLAUSE_KEY the rest of the site uses, so it can't drift."""
    from src.report.reel_copy import TEMPLATE as REEL_TEMPLATE

    for lang in LANGS:
        S = STRINGS[lang]
        reel_verdict = S["REEL_VERDICT_SIG"] if data_tokens["GAP_CLAUSE_KEY"].endswith("SIG") else S["REEL_VERDICT_OPEN"]
        tokens = {
            **S,
            **data_tokens,
            **_LANG_META[lang],
            "REEL_VERDICT": reel_verdict,
            "GAP_CLAUSE": S[data_tokens["GAP_CLAUSE_KEY"]],
            "TWFE_CLAUSE": S[data_tokens["TWFE_CLAUSE_KEY"]],
        }
        page = REEL_TEMPLATE
        for _ in range(6):
            before = page
            for k, v in tokens.items():
                page = page.replace("{{" + k + "}}", str(v))
            if page == before:
                break
        leftover = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", page)))
        if leftover:
            raise ValueError(f"unresolved reel tokens in {lang} build: {leftover}")
        (SITE / ("reel.html" if lang == "en" else "reel.es.html")).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    print("[site]", build())
