"""Build the GitHub Pages report: data/processed parquet -> site/index.html.

Run locally (`uv run python -m src.report.build_site`) and in CI on push. CI does
NOT scrape — it only renders the committed parquet + snapshots into the site, so
it can't be IP-blocked. Everything in the page is derived deterministically here.

Token substitution: reports/writeup.md may contain {{tokens}} (e.g. the headline
number) which are filled from the computed effects so prose and charts never drift.
"""

from __future__ import annotations

import html

import shutil

import markdown
import plotly.io as pio

from src.analysis.descriptive import effect_by_type, load_processed
from src.paths import REPORTS, SITE, STOPPAGES_PARQUET
from src.report.methodology import build_appendix_html, small_n_notice
from src.snapshot import load_all_snapshots
from src.viz.charts import distribution_chart, effect_chart, trend_chart
from src.viz.static_charts import save_static_charts

PLOTLY_CDN = '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>'

PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup 2026 — Stoppage Momentum</title>
{cdn}
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         max-width: 860px; margin: 0 auto; padding: 24px; color: #1a1a1a; line-height: 1.55; }}
  h1, h2, h3 {{ line-height: 1.2; }} h1 {{ margin-bottom: .2em; }}
  .sub {{ color: #666; margin-top: 0; }}
  .chart {{ margin: 28px 0; }}
  table {{ border-collapse: collapse; }} td, th {{ border: 1px solid #ddd; padding: 6px 10px; }}
  code {{ background: #f4f4f4; padding: 1px 4px; border-radius: 3px; }}
  footer {{ color: #888; font-size: .85em; margin-top: 48px; border-top: 1px solid #eee; padding-top: 12px; }}
</style></head><body>
{body}
<footer>Generated from <code>data/processed/stoppages.parquet</code>. Derived data only;
raw provider payloads not redistributed. Code: MIT.</footer>
</body></html>
"""


def _fmt(x: float | None) -> str:
    return "n/a" if x is None or x != x else f"{x:+.1f}"


def _headline_tokens(effects: list[dict]) -> dict[str, str]:
    hyd = next((e for e in effects if e["stoppage_type"] == "hydration"), None)
    if not hyd or hyd["n"] == 0:
        return {"HEADLINE": "Not enough data yet.", "HYD_N": "0", "HYD_MEAN": "n/a", "HYD_CI": "n/a"}
    sign = "away from" if hyd["mean_delta"] < 0 else "toward"
    return {
        "HEADLINE": (
            f"Across {hyd['n']} hydration breaks, momentum shifted {sign} the team that was on "
            f"top by {_fmt(hyd['mean_delta'])} on average "
            f"(95% CI {_fmt(hyd['ci_lo'])}..{_fmt(hyd['ci_hi'])})."
        ),
        "HYD_N": str(hyd["n"]),
        "HYD_MEAN": _fmt(hyd["mean_delta"]),
        "HYD_CI": f"{_fmt(hyd['ci_lo'])}..{_fmt(hyd['ci_hi'])}",
    }


def _effects_table(effects: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(e['stoppage_type'])}</td><td>{e['n']}</td>"
        f"<td>{_fmt(e['mean_delta'])}</td><td>{_fmt(e['ci_lo'])}..{_fmt(e['ci_hi'])}</td></tr>"
        for e in effects
    )
    return (
        "<table><thead><tr><th>Stoppage type</th><th>n (on top)</th>"
        "<th>Mean Δ</th><th>95% CI</th></tr></thead><tbody>" + rows + "</tbody></table>"
    )


def _per_match_section() -> str:
    """Embed the locally-generated per-match momentum grid (committed in reports/figures/)."""
    src = REPORTS / "figures" / "per_match_momentum.png"
    if not src.exists():
        return ""
    dest = SITE / "figures"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest / "per_match_momentum.png")
    return (
        "<h2>Per-match momentum</h2>"
        "<p>How momentum moved in every match so far (blue = home on top, orange = away); "
        "dashed lines mark stoppages.</p>"
        '<p><img src="figures/per_match_momentum.png" alt="Per-match momentum grid" style="max-width:100%"></p>'
    )


def build() -> str:
    df = load_processed() if STOPPAGES_PARQUET.exists() else None
    SITE.mkdir(parents=True, exist_ok=True)

    if df is None or df.is_empty():
        body = "<h1>World Cup 2026 — Stoppage Momentum</h1><p>No data yet. Check back after the next match.</p>"
        out = SITE / "index.html"
        out.write_text(PAGE.format(cdn=PLOTLY_CDN, body=body), encoding="utf-8")
        return str(out)

    effects = effect_by_type(df)
    tokens = _headline_tokens(effects)

    # writeup.md with {{token}} substitution -> HTML
    md_path = REPORTS / "writeup.md"
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else "# World Cup 2026 — Stoppage Momentum\n\n{{HEADLINE}}"
    for k, v in tokens.items():
        md_text = md_text.replace("{{" + k + "}}", v)
    prose_html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    def div(fig):
        return f'<div class="chart">{pio.to_html(fig, include_plotlyjs=False, full_html=False)}</div>'

    # Static publication PNGs (for download / social sharing) alongside the
    # interactive plotly charts; the methodology appendix + small-N caveat round
    # out the page.
    save_static_charts(df)  # -> site/figures/*.png (stable filenames)
    static_section = (
        '<details><summary>Static charts (for sharing)</summary>'
        '<p><img src="figures/effect_by_type.png" alt="Effect by stoppage type" style="max-width:100%">'
        '<img src="figures/distribution.png" alt="Distribution of momentum delta" style="max-width:100%">'
        "</p></details>"
    )

    body = (
        prose_html
        + small_n_notice(df)
        + "<h2>Effect by stoppage type</h2>"
        + _effects_table(effects)
        + div(effect_chart(effects))
        + div(distribution_chart(df))
        + div(trend_chart(load_all_snapshots()))
        + _per_match_section()
        + static_section
        + build_appendix_html()
    )
    out = SITE / "index.html"
    out.write_text(PAGE.format(cdn=PLOTLY_CDN, body=body), encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    print("[site]", build())
