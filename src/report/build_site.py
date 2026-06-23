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

import polars as pl

from src.analysis.descriptive import (
    cluster_bootstrap_ci,
    effect_by_type,
    load_processed,
    on_top_rows,
    pre_level_r2,
)
from src.paths import PROCESSED, REPORTS, SITE, STOPPAGES_PARQUET
from src.report.editorial_copy import TEMPLATE
from src.report.i18n import COUNTRIES, FRAG, JS, LABELS, LANGS, MONTHS, STAGE, STRINGS, TYPES
from src.snapshot import load_all_snapshots

ACCENT = "#E5482E"
INK = "#1A1813"
SCALE = 32.0  # momentum axis: 0 .. -32
PAGES_URL = "https://github.com/valternunez/wc2026-momentum"
SITE_BASE = "https://valternunez.github.io/wc2026-momentum/"

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


def _lang_toggle(lang: str) -> str:
    """Footer English ⇄ Español switch: the current language inert, the other linked."""
    base = "font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em"
    on = f"{base};color:#E5C9A0;font-weight:600"
    off = f"{base};color:#7E776A;text-decoration:none;border-bottom:1px solid rgba(229,72,46,.35)"
    en = (f'<span style="{on}">English</span>' if lang == "en"
          else f'<a href="index.html" style="{off}">English</a>')
    es = (f'<span style="{on}">Español</span>' if lang == "es"
          else f'<a href="index.es.html" style="{off}">Español</a>')
    sep = f'<span style="{base};color:#5A5547;padding:0 8px">·</span>'
    return f'<div style="margin:0 0 18px">{en}{sep}{es}</div>'


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
            <span style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><span style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.1em;color:#5A5547">M{idx:02d}{f" · {date}" if date else ""}</span><span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#C9BFA6">↗</span></span>
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
                f'<span style="font-family:\'IBM Plex Sans\',sans-serif;font-size:14px;color:#1A1813">{h} {vs} {a}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:#1A1813;white-space:nowrap">'
                f'{team} {sign}{abs(drop):.0f} '
                f'<span style="color:#5A5547">{frm} +{r["momentum_pre_5min_mean"]:.0f} · {int(r["clock_minute"])}\'</span></span></button>')

    return f"""
      <div style="margin:4px 0 32px">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,258px),1fr));gap:22px 44px">
          <div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:6px">{F["extremes_biggest"]}</div>
            {"".join(row(r) for r in biggest)}
          </div>
          <div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#5A5547;font-weight:600;margin-bottom:6px">{F["extremes_quietest"]}</div>
            {"".join(row(r) for r in quietest)}
          </div>
        </div>
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
    """Short, purely descriptive note on this match's momentum (no causal claims)."""
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
        lead_delta = d if pre > 0 else -d  # from the leader's perspective
        m = int(r["clock_minute"])
        key = "exp_lost" if lead_delta < 0 else "exp_pushed"
        parts.append(F[key].format(m=m, leader=leader, x=f"{abs(lead_delta):.0f}"))
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
    p26 = _placebo_meanci("placebo2026.parquet")
    if p26:
        rows_data.append((F["cc_p26_label"], F["cc_p26_sub"],
                          p26[0], p26[1], p26[2], p26[3], p26[4], ACCENT, False, F["tip_placebo"]))
    cwc = _placebo_meanci("cwc2025_placebo.parquet")
    if cwc:
        rows_data.append((F["cc_cwc_label"], F["cc_cwc_sub"],
                          cwc[0], cwc[1], cwc[2], cwc[3], cwc[4], "#46412F", True, None))
    w22 = _placebo_meanci("wc2022_placebo.parquet")
    if w22:
        rows_data.append((F["cc_wc22_label"], F["cc_wc22_sub"],
                          w22[0], w22[1], w22[2], w22[3], w22[4], "#8A8268", True, None))

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
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#9A927E">{n_lbl}</span>
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
            'font-size:10.5px;color:#5A5547;margin-top:2px"><span>−30</span><span>−20</span><span>−10</span><span>0</span></div>')
    return '<div style="margin:26px 0 8px">' + "".join(out) + axis + "</div>"


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


def _trend_section(snapshots: list[dict], hyd_mean: float | None, hyd_n: int, updated: str, F: dict) -> str:
    est = f"−{abs(hyd_mean):.1f}" if hyd_mean is not None else "—"
    extra = F["trend_extra"].format(k=len(snapshots)) if len(snapshots) >= 2 else ""
    body = F["trend_sentence"].format(updated=updated, est=est, n=hyd_n, extra=extra)
    return f"""
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6">
    <div style="max-width:840px;margin:0 auto;padding:46px 40px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:16px">{F["trend_label"]}</div>
      <p style="font-family:'Newsreader',serif;font-size:20px;line-height:1.6;color:#2B2820;max-width:60ch">{body}</p>
    </div>
  </section>"""


def build() -> str:
    SITE.mkdir(parents=True, exist_ok=True)
    site_figures = SITE / "figures"
    site_figures.mkdir(parents=True, exist_ok=True)
    # social/share assets live at the site root for absolute OG URLs (generated locally, committed)
    for icon in ("og.png", "og.es.png", "apple-touch-icon.png"):
        src = REPORTS / "figures" / icon
        if src.exists():
            shutil.copyfile(src, SITE / icon)

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
    nobreak = sorted(round(abs(x[0])) for x in (p26, cwc, w22) if x)
    r2 = pre_level_r2(df)
    heat = _heat_tokens(df)
    data_tokens = {
        **heat,
        "HEAT_GRID": _heat_grid(heat["HEAT_N"] != "0"),
        "HERO_DELTA": _absround(hyd.get("mean_delta")) if hyd else "—",
        "P26_DELTA": _absround(p26[0] if p26 else None),
        "CWC_DELTA": _absround(cwc[0] if cwc else None),
        "WC22_DELTA": _absround(w22[0] if w22 else None),
        "NOBREAK_LO": str(nobreak[0]) if nobreak else "—",
        "NOBREAK_HI": str(nobreak[-1]) if nobreak else "—",
        "PRE_R2": str(round(r2 * 100)) if r2 is not None else "—",
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
            "LANG_TOGGLE": _lang_toggle(lang),
            "SNAPSHOT_DATE": snap_date or updated,
            "SNAPSHOT_ISO": snap_date or "",
            "JS_STRINGS": json.dumps(JS[lang], ensure_ascii=False),
            "MB_DATA": _mb_data(df, F, TYPES[lang], lang),
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
    return first_out or str(SITE / "index.html")


if __name__ == "__main__":
    print("[site]", build())
