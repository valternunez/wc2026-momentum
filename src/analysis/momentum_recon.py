"""Offline validation: how much of FotMob momentum is explained by shots alone?

FotMob's momentum is an xT model (`debugTitle: "Using xT SA-version"`) built from the full
pass/carry event stream FotMob has on its backend but does NOT expose in the public payload —
we only get the shotmap. So we can't reproduce the curve exactly. Instead we build a
recency-weighted shot-xG threat differential (home minus away) and correlate it against the
published momentum curve. This is a LOWER BOUND on reconstructability: xT also rewards ball
progressions between shots, which shots-only can't see.

Local-only (reads data/raw/fotmob, which is gitignored). Run:
    uv run python -m src.analysis.momentum_recon
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median
from typing import Any

from src.paths import RAW
from src.scrape import fotmob

RAW_FOTMOB = RAW / "fotmob"
TAUS = (3.0, 5.0, 8.0, 12.0)  # exponential-decay time constants (minutes) to sweep


def parse_shots(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-shot threat from the FotMob shotmap: minute (incl. added), xG, home flag."""
    g = raw.get("general") or {}
    home_id = (g.get("homeTeam") or {}).get("id")
    shots_raw = ((raw.get("content") or {}).get("shotmap") or {}).get("shots") or []
    out = []
    for s in shots_raw:
        xg, m = s.get("expectedGoals"), s.get("min")
        if xg is None or m is None:
            continue
        out.append({"m": float(m) + float(s.get("minAdded") or 0),
                    "xg": float(xg), "home": s.get("teamId") == home_id})
    return out


def threat_proxy(shots: list[dict], max_min: int, tau: float = 6.0) -> list[float]:
    """Per-minute home-positive threat: sum of past shots' xG with exp decay (constant tau)."""
    series = []
    for t in range(int(max_min) + 1):
        v = 0.0
        for s in shots:
            if s["m"] <= t:
                v += math.exp(-(t - s["m"]) / tau) * s["xg"] * (1.0 if s["home"] else -1.0)
        series.append(v)
    return series


def _momentum_series(mom: list[dict], max_min: int) -> list[float]:
    d = {int(x["minute"]): float(x["value"]) for x in mom}
    out, last = [], 0.0
    for t in range(max_min + 1):
        last = d.get(t, last)
        out.append(last)
    return out


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 3:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    return cov / math.sqrt(va * vb) if va > 0 and vb > 0 else float("nan")


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def _spearman(a: list[float], b: list[float]) -> float:
    return _pearson(_ranks(a), _ranks(b))


def correlate(proxy: list[float], momentum: list[float], max_lag: int = 3) -> dict[str, float]:
    n = min(len(proxy), len(momentum))
    p, mo = proxy[:n], momentum[:n]
    r, rho = _pearson(p, mo), _spearman(p, mo)
    best_l, best_r = 0, r
    for lag in range(-max_lag, max_lag + 1):  # lag>0: momentum leads the proxy
        pa, mb = (p[: n - lag], mo[lag:n]) if lag >= 0 else (p[-lag:n], mo[: n + lag])
        if len(pa) < 5:
            continue
        rr = _pearson(pa, mb)
        if not math.isnan(rr) and abs(rr) > abs(0 if math.isnan(best_r) else best_r):
            best_l, best_r = lag, rr
    return {"pearson": r, "spearman": rho, "best_lag": best_l, "best_lag_r": best_r}


def summarize(raw_dir: Path = RAW_FOTMOB, tau: float = 6.0) -> list[dict[str, Any]]:
    rows = []
    for p in sorted(Path(raw_dir).glob("*.json")):
        raw = json.loads(p.read_text(encoding="utf-8"))
        mom, shots = fotmob.parse_momentum(raw), parse_shots(raw)
        if not mom or not shots:
            continue
        max_min = int(max(x["minute"] for x in mom))
        c = correlate(threat_proxy(shots, max_min, tau), _momentum_series(mom, max_min))
        rows.append({"id": p.stem, "n_shots": len(shots), **c})
    return rows


def _overlay_png(raw_dir: Path, mid: str, tau: float, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw = json.loads((Path(raw_dir) / f"{mid}.json").read_text(encoding="utf-8"))
    g = raw.get("general") or {}
    home = (g.get("homeTeam") or {}).get("name", "Home")
    away = (g.get("awayTeam") or {}).get("name", "Away")
    mom = fotmob.parse_momentum(raw)
    max_min = int(max(x["minute"] for x in mom))
    mo = _momentum_series(mom, max_min)
    px = threat_proxy(parse_shots(raw), max_min, tau)

    def z(s):
        n = len(s); m = sum(s) / n
        sd = (sum((x - m) ** 2 for x in s) / n) ** 0.5 or 1.0
        return [(x - m) / sd for x in s]

    xs = list(range(max_min + 1))
    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=130)
    ax.axhline(0, color="#888", lw=0.6)
    ax.plot(xs, z(mo), color="#1A1813", lw=1.8, label="FotMob momentum (xT)")
    ax.plot(xs, z(px), color="#E5482E", lw=1.6, ls="--", label="Our shot-xG proxy")
    r = _pearson(mo, px)
    ax.set_title(f"{home} v {away} — FotMob momentum vs shot-xG proxy (r={r:.2f}, tau={tau:.0f})",
                 fontsize=10)
    ax.set_xlabel("minute"); ax.set_yticks([]); ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout(); out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out); plt.close(fig)


if __name__ == "__main__":
    print(f"Shots-only reconstruction of FotMob momentum  (n matches with shots+momentum)\n")
    print(f"{'tau':>5} | {'median r':>9} | {'median rho':>10} | {'median best-lag r':>17}")
    print("-" * 52)
    best_tau, best_med = TAUS[0], -1.0
    per_tau = {}
    for tau in TAUS:
        rows = summarize(tau=tau)
        med_r = median(x["pearson"] for x in rows if not math.isnan(x["pearson"]))
        med_rho = median(x["spearman"] for x in rows if not math.isnan(x["spearman"]))
        med_bl = median(x["best_lag_r"] for x in rows if not math.isnan(x["best_lag_r"]))
        per_tau[tau] = (rows, med_r, med_rho, med_bl)
        print(f"{tau:>5.0f} | {med_r:>9.3f} | {med_rho:>10.3f} | {med_bl:>17.3f}")
        if med_r > best_med:
            best_med, best_tau = med_r, tau

    rows, med_r, med_rho, med_bl = per_tau[best_tau]
    lags = [x["best_lag"] for x in rows]
    print(f"\nBest tau = {best_tau:.0f}  (median Pearson r = {med_r:.3f}, "
          f"median Spearman = {med_rho:.3f}, n = {len(rows)})")
    print(f"median best-lag r = {med_bl:.3f}; median lag = {median(lags):+.0f} min "
          f"(positive = momentum leads the shot)")
    # representative overlay = match whose r is closest to the median
    rows_sorted = sorted(rows, key=lambda x: abs(x["pearson"] - med_r))
    rep = rows_sorted[0]["id"]
    out = Path("data/interim/recon_overlay.png")  # gitignored; a throwaway diagnostic
    _overlay_png(RAW_FOTMOB, rep, best_tau, out)
    print(f"\nOverlay for representative match {rep} -> {out}")
