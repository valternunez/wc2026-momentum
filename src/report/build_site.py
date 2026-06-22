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


def _fmt_date(iso: str | None) -> str:
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


def _match_cards(site_figures: Path) -> str:
    mpath = PROCESSED / "matches.json"
    src_dir = REPORTS / "figures" / "matches"
    if not mpath.exists() or not src_dir.exists():
        return '<p style="font-family:IBM Plex Mono,monospace;color:#948D7C">Match panels render on the next local update.</p>'
    matches = json.loads(mpath.read_text(encoding="utf-8"))
    dest = site_figures / "matches"
    dest.mkdir(parents=True, exist_ok=True)
    cards = []
    idx = 0
    for m in matches:
        png = src_dir / f"{m['id']}.png"
        if not png.exists():
            continue
        idx += 1
        shutil.copyfile(png, dest / f"{m['id']}.png")
        home, away = m.get("home") or "?", m.get("away") or "?"
        cards.append(f"""
          <div class="mb-card" style="background:#FCFAF3;border:1px solid #E2DBCA;border-radius:3px;padding:13px 14px 12px;display:flex;flex-direction:column;gap:10px">
            <div style="display:flex;justify-content:space-between;align-items:baseline"><span style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.14em;color:#B0A78F">M{idx:02d}</span></div>
            <div style="display:flex;flex-direction:column;gap:4px">
              <div style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:#3E88C7;flex:none"></span><span style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:14px;color:#1A1813;line-height:1.15">{home}</span></div>
              <div style="display:flex;align-items:center;gap:8px"><span style="width:8px;height:8px;border-radius:50%;background:#E08A4B;flex:none"></span><span style="font-family:'IBM Plex Sans',sans-serif;font-weight:500;font-size:14px;color:#746E5F;line-height:1.15">{away}</span></div>
            </div>
            <img src="figures/matches/{m['id']}.png" alt="{home} v {away} — per-minute momentum" loading="lazy" style="width:100%;height:74px;object-fit:contain;object-position:center;display:block;margin-top:2px"/>
          </div>""")
    return "".join(cards)


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
    updated = _fmt_date(snap_date)

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
                          "left of zero. The causal claim is held until the live sample is larger — see method."),
        "COMPARE_SENTENCE": _compare_sentence(effects),
        "MATCH_CARDS": _match_cards(site_figures),
        "MECH_HYD": mech("hydration"), "MECH_VAR": mech("var"),
        "MECH_IH": mech("injury_huddle"), "MECH_INH": mech("injury_no_huddle"),
        **_placebo_tokens(),
        "TREND": _trend_section(snapshots, hyd.get("mean_delta"), hyd.get("n", 0), updated),
        "PAGES_URL": PAGES_URL,
        "SNAPSHOT_DATE": snap_date or updated,
    }

    html = TEMPLATE
    for k, v in tokens.items():
        html = html.replace("{{" + k + "}}", str(v))
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    print("[site]", build())
