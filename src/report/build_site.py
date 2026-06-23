"""Build the editorial report (site/index.html) from the committed dataset.

Renders the supplied editorial design (src/report/editorial_copy.TEMPLATE) by
substituting {{TOKENS}} with values computed live from data/processed/*. CI-safe:
uses only base deps (polars/numpy/scipy) — no scraping, no pandas/statsmodels.
Per-match panel images are generated locally and committed; here we just copy and
embed them.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, effect_by_type, load_processed, on_top_rows
from src.paths import PROCESSED, REPORTS, SITE, STOPPAGES_PARQUET
from src.report.editorial_copy import TEMPLATE
from src.snapshot import load_all_snapshots

ACCENT = "#E5482E"
INK = "#1A1813"
SCALE = 32.0  # momentum axis: 0 .. -32
PAGES_URL = "https://github.com/valternunez/wc2026-momentum"

_LABELS = {
    "hydration": "Hydration break",
    "var": "VAR review",
    "injury_huddle": "Injury · with huddle",
    "injury_no_huddle": "Injury · no huddle",
}
_ORDER = ["hydration", "var", "injury_huddle", "injury_no_huddle"]
_MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _fmt_date_iso(iso: str | None) -> str:
    """ISO date (YYYY-MM-DD) → '22 June 2026' (falls back to today)."""
    if not iso:
        d = datetime.now(timezone.utc)
        return f"{d.day} {_MONTHS[d.month]} {d.year}"
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {_MONTHS[d.month]} {d.year}"


def _money_rows(effects: list[dict]) -> str:
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
            <span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:16px;color:{color}">{_LABELS[stype]}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">n = {e['n']}</span>
          </div>
          <div style="position:relative;height:30px">
            <div style="position:absolute;top:13px;height:4px;right:0;width:{mean_pct:.2f}%;background:{color};opacity:{1 if is_hl else .85}"></div>
            <div style="position:absolute;top:9px;height:12px;right:{lo_pct:.2f}%;width:{hi_pct - lo_pct:.2f}%;border-left:1px solid {color};border-right:1px solid {color};background:{color};opacity:{.16 if is_hl else .12}"></div>
            <div style="position:absolute;top:9px;width:12px;height:12px;border-radius:50%;right:calc({mean_pct:.2f}% - 6px);background:{color};box-shadow:0 0 0 3px #EFEBDF"></div>
            <span style="position:absolute;top:-2px;font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:15px;color:{color};right:calc({mean_pct:.2f}% + 14px)">{mean:.1f}</span>
          </div>
        </div>""")
    return "".join(out)


_KO_LABEL = {"1/16": "Round of 32", "1/8": "Round of 16", "1/4": "Quarter-finals",
             "1/2": "Semi-finals", "bronze": "Third-place play-off", "final": "Final"}
_KO_ORDER = {"1/16": 1, "1/8": 2, "1/4": 3, "1/2": 4, "bronze": 5, "final": 6}


def _fmt_date_epoch(ts) -> str:
    """Epoch seconds → DD/MM/YYYY (UTC, kickoff date)."""
    if not ts:
        return ""
    from datetime import datetime, timezone
    try:
        ts = int(float(ts))
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d/%m/%Y")


def _stage_meta(league: str | None, rnd) -> tuple[str, tuple]:
    """(display label, sort key) for a match's stage. Groups first (A→L), then knockouts in order."""
    league = league or ""
    if "Grp." in league:
        letter = league.split("Grp.")[-1].strip()
        return (f"Group {letter}", (0, letter))
    key = rnd.lower() if isinstance(rnd, str) else rnd
    if key in _KO_LABEL:
        return (_KO_LABEL[key], (1, _KO_ORDER[key]))
    return ("Other matches", (2, 0))


def _match_cards(site_figures: Path) -> str:
    mpath = PROCESSED / "matches.json"
    src_dir = REPORTS / "figures" / "matches"
    if not mpath.exists() or not src_dir.exists():
        return '<p style="font-family:IBM Plex Mono,monospace;color:#948D7C">Match panels render on the next local update.</p>'
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
        home, away = m.get("home") or "?", m.get("away") or "?"
        date = _fmt_date_epoch(m.get("ts"))
        card = f"""
          <div class="mb-card" data-mid="{m['id']}" role="button" tabindex="0" aria-label="{home} v {away} — open chart" style="background:#FCFAF3;border:1px solid #E2DBCA;border-radius:3px;padding:13px 14px 12px;display:flex;flex-direction:column;gap:10px;cursor:pointer">
            <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><span style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.1em;color:#B0A78F">M{idx:02d}{f" · {date}" if date else ""}</span><span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#C9BFA6">↗</span></div>
            <div style="display:flex;flex-direction:column;gap:4px">
              <div style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:#3E88C7;flex:none"></span><span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:14px;color:#1A1813;line-height:1.15">{home}</span></div>
              <div style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:#E08A4B;flex:none"></span><span style="font-family:'IBM Plex Sans',sans-serif;font-weight:500;font-size:14px;color:#746E5F;line-height:1.15">{away}</span></div>
            </div>
            <img src="figures/matches/{m['id']}.png" alt="{home} v {away} — per-minute momentum" loading="lazy" style="width:100%;height:74px;object-fit:contain;object-position:center;display:block;margin-top:2px"/>
          </div>"""
        label, order = _stage_meta(m.get("league"), m.get("stage"))
        g = groups.setdefault(label, {"order": order, "cards": []})
        g["cards"].append(card)

    if not groups:
        return '<p style="font-family:IBM Plex Mono,monospace;color:#948D7C">Match panels render on the next local update.</p>'

    out = []
    for label in sorted(groups, key=lambda lb: groups[lb]["order"]):
        cards = groups[label]["cards"]
        out.append(
            '<details class="grp" open>'
            f'<summary class="grp-h"><span>{label}</span><span class="grp-n">{len(cards)}</span></summary>'
            '<div class="grp-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,210px),1fr));gap:14px">'
            + "".join(cards) + "</div></details>"
        )
    return "".join(out)


def _match_names() -> dict[str, tuple[str, str]]:
    """{match_id: (home, away)} from the committed momentum.json."""
    p = PROCESSED / "momentum.json"
    if not p.exists():
        return {}
    return {str(m["id"]): (m.get("home") or "?", m.get("away") or "?")
            for m in json.loads(p.read_text(encoding="utf-8"))}


def _extremes_block(df: pl.DataFrame, names: dict[str, tuple[str, str]]) -> str:
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
    if len(recs) < 4:
        return ""
    biggest, quietest = recs[:5], list(reversed(recs[-5:]))

    def row(r: dict) -> str:
        mid = str(r["match_id"]); h, a = names.get(mid, ("?", "?"))
        drop = r["momentum_delta"]; sign = "−" if drop < 0 else "+"
        return (f'<div class="mb-card" data-mid="{mid}" role="button" tabindex="0" '
                f'aria-label="{h} v {a} — open chart" style="cursor:pointer;display:flex;'
                f'justify-content:space-between;align-items:baseline;gap:12px;padding:9px 0;border-bottom:1px solid #E6E0CF">'
                f'<span style="font-family:\'IBM Plex Sans\',sans-serif;font-size:14px;color:#1A1813">{h} v {a}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:#1A1813;white-space:nowrap">'
                f'{r["team"]} {sign}{abs(drop):.0f} '
                f'<span style="color:#A89F88">from +{r["momentum_pre_5min_mean"]:.0f} · {int(r["clock_minute"])}\'</span></span></div>')

    note = ("Why matches and not teams? Each side has only one-to-four breaks so far, and about 77% of "
            "the swing is set by how high a team was already riding when the whistle went — so a team "
            "table would mostly rank who happened to be dominant in those minutes, not who's break-prone.")
    return f"""
      <div style="margin:4px 0 32px">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,258px),1fr));gap:22px 44px">
          <div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:6px">Biggest swings</div>
            {"".join(row(r) for r in biggest)}
          </div>
          <div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#5A5547;font-weight:600;margin-bottom:6px">Quietest breaks</div>
            {"".join(row(r) for r in quietest)}
          </div>
        </div>
        <p style="font-family:'Newsreader',serif;font-size:17px;line-height:1.55;color:#5A5547;margin-top:20px;max-width:64ch">{note}</p>
      </div>"""


def _compare_sentence(effects: list[dict]) -> str:
    by = {e["stoppage_type"]: abs(e["mean_delta"]) for e in effects if e["n"]}
    hyd = by.get("hydration")
    var = by.get("var")
    inh = by.get("injury_no_huddle")
    hyd_n = next((e["n"] for e in effects if e["stoppage_type"] == "hydration"), 0)
    if not hyd:
        return "Not enough data yet to compare stoppage types."
    bits = []
    if var:
        bits.append(f"about {round((hyd / var - 1) * 100)}% more momentum than a VAR review")
    if inh:
        bits.append(f"roughly {hyd / inh:.1f}× a no-huddle injury stoppage")
    comp = " and ".join(bits) if bits else "the largest swing of any stoppage type"
    return (f"A hydration break costs the leading side {comp}. And it isn't only noise at the edges: "
            f"with {hyd_n} breaks logged, the hydration estimate is the tightest of the four — the "
            f"more data arrives, the less it moves.")


def _match_explanation(df: pl.DataFrame, mid: str, home: str, away: str) -> str:
    """Short, purely descriptive note on this match's momentum (no causal claims)."""
    if df is None or df.is_empty():
        return f"Per-minute momentum for {home} (home, blue) vs {away} (away, orange)."
    rows = (df.filter((pl.col("match_id") == str(mid)) & (pl.col("is_home") == True))  # noqa: E712
            .sort("clock_minute").to_dicts())
    if not rows:
        return f"Per-minute momentum for {home} vs {away}. No stoppages detected."
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
        if lead_delta < 0:
            parts.append(f"At the {m}' hydration break {leader} were on top, then lost "
                         f"{abs(lead_delta):.0f} momentum over the next five minutes.")
        else:
            parts.append(f"At the {m}' hydration break {leader} were on top and pushed "
                         f"{abs(lead_delta):.0f} further ahead.")
    sw = max(rows, key=lambda r: abs(r.get("momentum_delta") or 0))
    if sw.get("momentum_delta") is not None:
        parts.append(f"Biggest post-stoppage swing: {abs(sw['momentum_delta']):.0f} at the "
                     f"{int(sw['clock_minute'])}' {sw['stoppage_type'].replace('_', ' ')}.")
    return " ".join(parts) or f"Per-minute momentum for {home} vs {away}."


def _mb_data(df: pl.DataFrame) -> str:
    """Augment committed momentum.json with a per-match explanation; return JSON for the modal."""
    p = PROCESSED / "momentum.json"
    if not p.exists():
        return "[]"
    data = json.loads(p.read_text(encoding="utf-8"))
    for m in data:
        m["explain"] = _match_explanation(df, m["id"], m.get("home") or "Home", m.get("away") or "Away")
    return json.dumps(data, ensure_ascii=False)


def _placebo_tokens() -> dict[str, str]:
    p = PROCESSED / "historical_placebo.parquet"
    if not p.exists():
        return {"PLACEBO_MEAN": "—", "PLACEBO_CI": "pending", "PLACEBO_N": ""}
    df = pl.read_parquet(p)
    top = on_top_rows(df)
    mean, lo, hi = cluster_bootstrap_ci(top)
    return {
        "PLACEBO_MEAN": f"{mean:+.3f}",
        "PLACEBO_CI": f"95% CI {lo:+.3f} … {hi:+.3f}",
        "PLACEBO_N": f"{top.height} on-top stoppages · {top['match_id'].n_unique()} matches",
    }


def _cwc_placebo_tokens() -> dict[str, str]:
    """CWC 2025 same-units placebo (FotMob momentum scale, directly comparable to 2026)."""
    p = PROCESSED / "cwc2025_placebo.parquet"
    if not p.exists():
        return {"CWC_MEAN": "—", "CWC_CI": "pending", "CWC_N": ""}
    df = pl.read_parquet(p)
    top = on_top_rows(df)
    mean, lo, hi = cluster_bootstrap_ci(top)
    return {
        "CWC_MEAN": f"{mean:+.1f}",
        "CWC_CI": f"95% CI {lo:+.1f} … {hi:+.1f}",
        "CWC_N": f"{top.height} on-top stoppages · {top['match_id'].n_unique()} matches",
    }


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


def _info(tip: str) -> str:
    """A small accessible info-tooltip trigger (ⓘ). `tip` is plain text (no double quotes)."""
    return f'<button type="button" class="info" aria-label="What does this mean?" data-tip="{tip}">i</button>'


_TIP_READ = ("How to read this: the dot is the average momentum drop for the team that was on top; "
             "the faint bar around it is the 95% range — where the true value very likely sits given "
             "how few matches we have so far. When two bars overlap a lot, those numbers aren't "
             "meaningfully different yet.")
_TIP_PLACEBO = ("The exact same 2026 matches, but measured at random quiet minutes with no break "
                "(around 10', 35', 55' and 80'). It shows how much the leading team fades with no "
                "whistle at all — the pure cool-off baseline, i.e. regression to the mean.")


def _compare_chart(effects: list[dict]) -> str:
    """Dot-and-whisker comparison: the 2026 break drop vs no-break baselines, same FotMob scale."""
    rows_data = []
    hyd = {e["stoppage_type"]: e for e in effects}.get("hydration")
    if hyd and hyd.get("n"):
        rows_data.append(("Hydration break", "World Cup 2026 · the headline",
                          hyd["mean_delta"], hyd["ci_lo"], hyd["ci_hi"], hyd["n"], None, ACCENT, True, _TIP_READ))
    p26 = _placebo_meanci("placebo2026.parquet")
    if p26:
        rows_data.append(("No break — same 2026 matches", "windowed at quiet, non-break minutes",
                          p26[0], p26[1], p26[2], p26[3], p26[4], ACCENT, False, _TIP_PLACEBO))
    cwc = _placebo_meanci("cwc2025_placebo.parquet")
    if cwc:
        rows_data.append(("No break — Club World Cup 2025", "same US summer · at the 22′/67′ marks",
                          cwc[0], cwc[1], cwc[2], cwc[3], cwc[4], "#46412F", True, None))
    w22 = _placebo_meanci("wc2022_placebo.parquet")
    if w22:
        rows_data.append(("No break — World Cup 2022", "cooler Qatar winter · at the 22′/67′ marks",
                          w22[0], w22[1], w22[2], w22[3], w22[4], "#8A8268", True, None))

    out = []
    for label, sub, mean, lo, hi, n, matches, color, solid, tip in rows_data:
        a, b = abs(lo), abs(hi)
        losp, hisp = min(min(a, b) / SCALE * 100, 100), min(max(a, b) / SCALE * 100, 100)
        mp = min(abs(mean) / SCALE * 100, 100)
        dot_fill = color if solid else "#EFEBDF"
        n_lbl = f"n = {n}" + (f" · {matches} matches" if matches else "")
        out.append(f"""
        <div style="position:relative;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px">
            <span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15.5px;color:{color}">{label}{_info(tip) if tip else ""}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#9A927E">{n_lbl}</span>
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.02em;color:#A89F88;margin-bottom:8px">{sub}</div>
          <div style="position:relative;height:26px">
            <div style="position:absolute;top:11px;height:4px;right:0;width:{mp:.2f}%;background:{color};opacity:{.9 if solid else .35}"></div>
            <div style="position:absolute;top:7px;height:12px;right:{losp:.2f}%;width:{hisp - losp:.2f}%;background:{color};opacity:.13"></div>
            <div style="position:absolute;top:7px;width:12px;height:12px;border-radius:50%;right:calc({mp:.2f}% - 6px);background:{dot_fill};border:2px solid {color};box-shadow:0 0 0 3px #EFEBDF"></div>
            <span style="position:absolute;top:-4px;font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:14px;color:{color};right:calc({mp:.2f}% + 14px)">{mean:.1f}</span>
          </div>
        </div>""")
    if not out:
        return ""
    axis = ('<div style="display:flex;justify-content:space-between;font-family:\'IBM Plex Mono\',monospace;'
            'font-size:10.5px;color:#B0A78F;margin-top:2px"><span>−30</span><span>−20</span><span>−10</span><span>0</span></div>')
    return '<div style="margin:26px 0 8px">' + "".join(out) + axis + "</div>"


def _wc2022_placebo_tokens() -> dict[str, str]:
    """2022 WC placebo via FotMob (same momentum scale as CWC/2026)."""
    p = PROCESSED / "wc2022_placebo.parquet"
    if not p.exists():
        return {"WC22F_MEAN": "—", "WC22F_CI": "pending", "WC22F_N": ""}
    df = pl.read_parquet(p)
    top = on_top_rows(df)
    mean, lo, hi = cluster_bootstrap_ci(top)
    return {
        "WC22F_MEAN": f"{mean:+.1f}",
        "WC22F_CI": f"95% CI {lo:+.1f} … {hi:+.1f}",
        "WC22F_N": f"{top.height} on-top · {top['match_id'].n_unique()} matches",
    }


def _heat_tokens(df: pl.DataFrame) -> dict[str, str]:
    """Per-match heat distribution for the 'did they need them?' note."""
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


def _trend_section(snapshots: list[dict], hyd_mean: float | None, hyd_n: int, updated: str) -> str:
    est = f"−{abs(hyd_mean):.1f}" if hyd_mean is not None else "—"
    extra = ""
    if len(snapshots) >= 2:
        extra = f" Tracking across {len(snapshots)} snapshots so far."
    return f"""
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6">
    <div style="max-width:840px;margin:0 auto;padding:46px 40px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:16px">Living analysis</div>
      <p style="font-family:'Newsreader',serif;font-size:20px;line-height:1.6;color:#2B2820;max-width:60ch">Recomputed every matchday from the committed dataset. As of {updated}, the hydration swing sits at <strong style="font-weight:600">{est}</strong> across {hyd_n} on-top breaks.{extra} Watch it as the knockouts arrive — wider stakes, more data, a tighter interval.</p>
    </div>
  </section>"""


def build() -> str:
    SITE.mkdir(parents=True, exist_ok=True)
    site_figures = SITE / "figures"
    site_figures.mkdir(parents=True, exist_ok=True)
    # social/share assets live at the site root for absolute OG URLs (generated locally, committed)
    for icon in ("og.png", "apple-touch-icon.png"):
        src = REPORTS / "figures" / icon
        if src.exists():
            shutil.copyfile(src, SITE / icon)

    if not STOPPAGES_PARQUET.exists() or load_processed().is_empty():
        out = SITE / "index.html"
        out.write_text("<!doctype html><meta charset=utf-8><title>WC2026 Momentum</title>"
                       "<body style='font-family:sans-serif;max-width:640px;margin:60px auto'>"
                       "<h1>WC2026 — Stoppage Momentum</h1><p>No data yet. Check back after the next match.</p>",
                       encoding="utf-8")
        return str(out)

    df = load_processed()
    effects = effect_by_type(df)
    by = {e["stoppage_type"]: e for e in effects}
    hyd = by.get("hydration", {})
    snapshots = load_all_snapshots()
    snap_date = snapshots[-1]["date"] if snapshots else None
    updated = _fmt_date_iso(snap_date)

    def mech(stype: str) -> str:
        e = by.get(stype)
        return f"{e['mean_delta']:.1f}" if e and e["n"] else "—"

    tokens = {
        "UPDATED_DATE": updated.upper(),
        "N_MATCHES": str(df["match_id"].n_unique()),
        "N_STOPPAGES": str(df["stoppage_id"].n_unique()),
        "HERO_DELTA": str(round(abs(hyd.get("mean_delta", 0)))) if hyd else "—",
        "HYD_N": str(hyd.get("n", 0)),
        "MONEY_ROWS": _money_rows(effects),
        "CI_CAPTION": "95% INTERVAL (CLUSTER BOOTSTRAP)",
        "INTERVAL_NOTE": ("Whiskers show the match-clustered bootstrap 95% interval; every interval sits "
                          "left of zero. The effect holds across 4–6-minute windows — but with few "
                          "match-clusters this far in, read the interval as indicative, not a p-value. "
                          "The causal claim is held until the live sample is larger — see method."),
        "COMPARE_SENTENCE": _compare_sentence(effects),
        "COMPARE_CHART": _compare_chart(effects),
        "EXTREMES": _extremes_block(df, _match_names()),
        "MATCH_CARDS": _match_cards(site_figures),
        "MECH_HYD": mech("hydration"), "MECH_VAR": mech("var"),
        "MECH_IH": mech("injury_huddle"), "MECH_INH": mech("injury_no_huddle"),
        **_placebo_tokens(),
        **_cwc_placebo_tokens(),
        **_wc2022_placebo_tokens(),
        **_heat_tokens(df),
        "TREND": _trend_section(snapshots, hyd.get("mean_delta"), hyd.get("n", 0), updated),
        "PAGES_URL": PAGES_URL,
        "SNAPSHOT_DATE": snap_date or updated,
        "SNAPSHOT_ISO": snap_date or "",
        "MB_DATA": _mb_data(df),
    }

    html = TEMPLATE
    for k, v in tokens.items():
        html = html.replace("{{" + k + "}}", str(v))
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    print("[site]", build())
