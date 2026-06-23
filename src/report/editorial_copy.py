"""Editorial report template (editable structure, separated from data & copy).

The full page is a `{{TOKEN}}`-templated HTML string. All human-readable copy lives in
`src/report/i18n.py` (English + Spanish); `build_site.py` selects a language, computes the
data tokens from the live committed data, and substitutes everything (plain str.replace over a
few passes, so the CSS braces in the <style> block are safe and one level of token-in-token
nesting — e.g. {{N_MATCHES}} inside a prose token — resolves).

Editorial integrity:
- All three pundit quotes are real and sourced (links inline, in i18n.py).
- Claims are kept to what the stats support: the *descriptive* ordering is real; the
  causal "huddle" reading is flagged as suggestive, not yet significant.
- Source of truth: FotMob per-minute momentum + ESPN commentary (not SofaScore).
- Bilingual: one structural template, two language string tables; EN -> index.html,
  ES -> index.es.html (sibling files keep relative asset paths valid).
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{META_TITLE}}</title>
<meta name="description" content="{{META_DESC}}">
<link rel="canonical" href="{{CANONICAL_URL}}">
<link rel="alternate" hreflang="en" href="https://valternunez.github.io/wc2026-momentum/">
<link rel="alternate" hreflang="es" href="https://valternunez.github.io/wc2026-momentum/index.es.html">
<link rel="alternate" hreflang="x-default" href="https://valternunez.github.io/wc2026-momentum/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{{OG_SITENAME}}">
<meta property="og:locale" content="{{OG_LOCALE}}">
<meta property="og:title" content="{{OG_TITLE}}">
<meta property="og:description" content="{{OG_DESC}}">
<meta property="og:url" content="{{OG_URL}}">
<meta property="og:image" content="{{OG_IMAGE}}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{{OG_ALT}}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{OG_TITLE}}">
<meta name="twitter:description" content="{{TW_DESC}}">
<meta name="twitter:image" content="{{OG_IMAGE}}">
<meta name="theme-color" content="#EFEBDF">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%231A1813'/><circle cx='16' cy='16' r='6' fill='%23E5482E'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#EFEBDF}
  a{color:inherit}
  [hidden]{display:none!important}
  ::selection{background:#E5482E;color:#FCFAF3}
  :focus-visible{outline:2px solid #E5482E;outline-offset:2px;border-radius:2px}
  @keyframes livepulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.78)}}
  .lp{animation:livepulse 1.8s ease-in-out infinite}
  .mb-card{transition:transform .14s ease, box-shadow .14s ease}
  .mb-card:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(26,24,19,.10)}
  #mb-table{margin-top:14px}
  #mb-table summary{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#5A5547;cursor:pointer;list-style:none;display:inline-flex;align-items:center;gap:6px}
  #mb-table summary::-webkit-details-marker{display:none}
  #mb-table summary::after{content:'+';color:#9A927E}
  #mb-table[open] summary::after{content:'–'}
  #mb-table table{border-collapse:collapse;width:100%;margin-top:10px;font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:#2B2820}
  #mb-table th,#mb-table td{text-align:left;padding:5px 10px 5px 0;border-bottom:1px solid #E6E0CF;white-space:nowrap}
  #mb-table th{color:#5A5547;font-weight:600;letter-spacing:.04em}
  .src{font-family:'IBM Plex Mono',monospace;color:#C03A22;text-decoration:none;border-bottom:1px solid #C03A22}
  .info{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border-radius:50%;border:1px solid #BBB29A;background:none;color:#8A8268;font-family:Georgia,'Newsreader',serif;font-style:italic;font-size:11px;font-weight:700;line-height:1;cursor:pointer;vertical-align:baseline;margin-left:5px;padding:0;transition:border-color .12s,color .12s,background .12s}
  .info:hover,.info:focus-visible{border-color:#E5482E;color:#fff;background:#E5482E;outline:none}
  #tip-pop{position:absolute;z-index:90;max-width:300px;background:#1A1813;color:#EFEBDF;font-family:'IBM Plex Sans',sans-serif;font-size:13px;line-height:1.5;padding:12px 15px;border-radius:5px;box-shadow:0 12px 34px rgba(26,24,19,.34);opacity:0;pointer-events:none;transition:opacity .12s}
  #tip-pop.on{opacity:1;pointer-events:auto}
  .mb-tabs{display:inline-flex;flex-wrap:wrap;gap:5px;margin-bottom:10px}
  .mb-tab{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:600;padding:7px 14px;border:1px solid #D2CAB6;border-radius:3px;background:#F4F0E5;color:#8A8268;cursor:pointer;transition:background .12s,color .12s,border-color .12s}
  .mb-tab.on{background:#1A1813;color:#EFEBDF;border-color:#1A1813}
  .mb-tab:hover:not(.on){border-color:#1A1813;color:#1A1813}
  details.grp{margin:28px 0 0}
  details.grp>summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:baseline;gap:12px;border-bottom:1px solid #D6CFBE;padding-bottom:8px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#1A1813;font-weight:600}
  details.grp>summary::-webkit-details-marker{display:none}
  details.grp>summary .grp-n{color:#5A5547;font-weight:400}
  details.grp>summary .grp-n::after{content:'  +';color:#5A5547}
  details.grp[open]>summary .grp-n::after{content:'  –'}
  details.grp>summary:hover{color:#E5482E}
  details.grp[open]>.grp-grid{margin-top:14px}
  @media (prefers-reduced-motion:reduce){ .lp{animation:none}.mb-card,.mb-tab,#tip-pop,.mb-seg button{transition:none}.mb-card:hover{transform:none} }
</style></head>
<body>
<article style="background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif;width:100%;min-height:100vh;overflow-x:hidden">

  <!-- MASTHEAD -->
  <header style="max-width:840px;margin:0 auto;padding:22px 40px 0;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#1A1813;font-weight:600">{{MAST_TITLE}}</div>
    <div style="display:flex;align-items:center;gap:9px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:#6B6557">
      <span class="lp" style="width:8px;height:8px;border-radius:50%;background:#E5482E;display:inline-block"></span>
      {{LIVE_UPDATED}} {{UPDATED_DATE}}
    </div>
  </header>
  <div id="freshness" hidden style="max-width:840px;margin:10px auto 0;padding:9px 16px;background:#F4ECD8;border:1px solid #E0C98F;border-radius:3px;font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.03em;color:#6B5A2E">⚠ {{FRESH_NOTE}} <b>{{UPDATED_DATE}}</b>.</div>
  <div style="max-width:840px;margin:14px auto 0;padding:0 40px"><div style="height:2px;background:#1A1813"></div></div>

  <!-- HERO -->
  <section style="max-width:840px;margin:0 auto;padding:56px 40px 30px">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:26px">{{HERO_KICKER}}</div>
    <h1 style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(46px,7.4vw,104px);line-height:.95;letter-spacing:-.015em;max-width:15ch;text-wrap:balance">{{HERO_H1}}</h1>
    <p style="font-family:'Newsreader',serif;font-size:clamp(20px,2.4vw,28px);line-height:1.45;max-width:760px;margin-top:30px;color:#332F26;text-wrap:pretty">{{HERO_LEDE}}</p>
    <div style="display:flex;gap:28px;flex-wrap:wrap;margin-top:34px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:#6B6557">
      <span>{{HERO_BYLINE}}</span>
      <span>{{HERO_META}}</span>
    </div>
  </section>

  <!-- HEADLINE STAT BAND -->
  <section style="background:#1A1813;color:#EFEBDF;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:54px 40px;display:flex;gap:48px;align-items:center;flex-wrap:wrap">
      <div style="flex:0 0 auto;display:flex;align-items:flex-start;gap:6px">
        <span style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(34px,6vw,72px);color:#E5482E;line-height:1;align-self:flex-start;margin-top:.18em">−</span>
        <span style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(96px,17vw,210px);line-height:.82;color:#E5482E;letter-spacing:-.02em">{{HERO_DELTA}}</span>
      </div>
      <div style="flex:1 1 320px;min-width:280px">
        <p style="font-family:'Newsreader',serif;font-size:clamp(21px,2.3vw,29px);line-height:1.4;color:#EFEBDF;max-width:34ch">{{BAND_CAPTION}}</p>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.07em;color:#A9A290;margin-top:18px;line-height:1.75">
          <div>{{BAND_SUB1}}</div>
          <div>{{BAND_SUB2}}</div>
        </div>
      </div>
    </div>
  </section>

  <!-- 01 — THE CLAIM -->
  <section style="max-width:840px;margin:0 auto;padding:64px 40px 18px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">{{S01_HEAD}}</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">{{S01_LEAD}}</p>
    <blockquote style="font-family:'Newsreader',serif;font-style:italic;font-size:clamp(24px,2.9vw,33px);line-height:1.34;color:#1A1813;border-left:3px solid #E5482E;padding:6px 0 6px 28px;margin:34px 0 16px">{{S01_QUOTE}}</blockquote>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.13em;color:#6B6557;text-transform:uppercase;padding-left:28px;margin-bottom:34px">{{S01_ATTR}}</div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820">{{S01_FOLLOW}}</p>
  </section>

  <!-- 02 — MONEY CHART -->
  <section style="max-width:840px;margin:0 auto;padding:50px 40px 30px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:10px">{{S02_HEAD}}</h2>
    <div style="border-left:3px solid #DDD6C5;padding:2px 0 2px 20px;margin:0 0 28px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#5A5547;margin-bottom:8px">{{S02_MOMLABEL}}</div>
      <p style="font-family:'Newsreader',serif;font-size:18px;line-height:1.55;color:#46412F">{{S02_MOMDEF}}</p>
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;line-height:1.6;letter-spacing:.02em;color:#5A5547;margin-top:12px">{{S02_MOMTECH}}</p>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.58;color:#2B2820;margin-bottom:40px">{{S02_LEAD}}</p>

    <div style="border-top:2px solid #1A1813;padding-top:30px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px;gap:16px;flex-wrap:wrap">
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.14em;color:#6B6557">{{S02_CHARTLABEL}}</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.1em;color:#6B6557">{{CI_CAPTION}}</span>
      </div>
      <div style="position:relative">
        <div style="position:absolute;inset:0;pointer-events:none">
          <div style="position:absolute;top:0;bottom:34px;right:0;width:1px;background:#1A1813"></div>
          <div style="position:absolute;top:0;bottom:34px;right:31.25%;width:1px;background:rgba(26,24,19,.14)"></div>
          <div style="position:absolute;top:0;bottom:34px;right:62.5%;width:1px;background:rgba(26,24,19,.14)"></div>
          <div style="position:absolute;top:0;bottom:34px;right:93.75%;width:1px;background:rgba(26,24,19,.14)"></div>
        </div>
        {{MONEY_ROWS}}
        <div style="position:relative;height:30px;margin-top:6px">
          <span style="position:absolute;right:0;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#1A1813;font-weight:600">0</span>
          <span style="position:absolute;right:31.25%;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">−10</span>
          <span style="position:absolute;right:62.5%;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">−20</span>
          <span style="position:absolute;right:93.75%;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">−30</span>
        </div>
      </div>
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#5A5547;margin-top:14px;line-height:1.6">{{INTERVAL_NOTE}}</p>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-top:34px">{{COMPARE_SENTENCE}}</p>
  </section>

  <!-- 03 — MATCH BY MATCH -->
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:60px 40px 56px">
      <div style="margin-bottom:34px">
        <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:18px">{{S03_HEAD}}</h2>
        <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.55;color:#2B2820;text-wrap:pretty">{{S03_LEAD}}</p>
      </div>
      <div style="margin-bottom:32px">
        <h3 style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#1A1813;font-weight:600;margin-bottom:6px">{{S03_EXTREMES_HEAD}}</h3>
        <p style="font-family:'Newsreader',serif;font-size:18px;line-height:1.5;color:#2B2820;margin-bottom:16px;max-width:64ch">{{S03_EXTREMES_LEAD}}</p>
        {{EXTREMES}}
      </div>
      <div style="display:flex;gap:26px;flex-wrap:wrap;align-items:center;margin-bottom:28px;font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.06em;color:#5A5547">
        <span style="display:flex;align-items:center;gap:8px"><span style="width:18px;height:10px;background:#9CC4E0;display:inline-block;border-radius:1px"></span>{{LEG_HOME}}</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:18px;height:10px;background:#EBC09A;display:inline-block;border-radius:1px"></span>{{LEG_AWAY}}</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #3E88C7;display:inline-block"></span>{{LEG_HYDRATION}}</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dotted #7A5CC0;display:inline-block"></span>{{LEG_VAR}}</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #E08A4B;display:inline-block"></span>{{LEG_INJURY}}</span>
      </div>
      {{MATCH_CARDS}}
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#5A5547;margin-top:24px;line-height:1.6">{{S03_FOOTNOTE}}</p>
    </div>
  </section>

  <!-- 04 — MECHANISM -->
  <section style="background:#1A1813;color:#EFEBDF">
    <div style="max-width:840px;margin:0 auto;padding:62px 40px">
      <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:18px">{{S04_HEAD}}</h2>
      <p style="font-family:'Newsreader',serif;font-size:clamp(22px,2.6vw,30px);line-height:1.42;color:#EFEBDF;margin-bottom:42px;text-wrap:pretty">{{S04_LEAD}}</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid rgba(255,255,255,.22)">
        <div style="padding:26px 30px 26px 0;border-right:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5482E;line-height:1">{{MECH_HYD}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">{{MECH_HYD_LABEL}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">{{MECH_HYD_DESC}}</p>
        </div>
        <div style="padding:26px 0 26px 30px">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_VAR}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">{{MECH_VAR_LABEL}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">{{MECH_VAR_DESC}}</p>
        </div>
        <div style="padding:26px 30px 26px 0;border-right:1px solid rgba(255,255,255,.14);border-top:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_IH}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">{{MECH_IH_LABEL}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">{{MECH_IH_DESC}}</p>
        </div>
        <div style="padding:26px 0 26px 30px;border-top:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_INH}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">{{MECH_INH_LABEL}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">{{MECH_INH_DESC}}</p>
        </div>
      </div>
      <p style="font-family:'Newsreader',serif;font-size:20px;line-height:1.6;color:#D8D2C2;margin-top:34px">{{S04_CONCL}}</p>
    </div>
  </section>

  <!-- 05 — THE CATCH -->
  <section style="max-width:840px;margin:0 auto;padding:64px 40px 18px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">{{S05_HEAD}}</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">{{S05_LEAD1}}</p>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:8px">{{S05_LEAD2}}</p>
    {{COMPARE_CHART}}
    <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;line-height:1.7;letter-spacing:.01em;color:#6B6557;background:#EAE5D6;border-left:3px solid #E5C9A0;padding:14px 16px;margin:14px 0 28px">{{S05_CAVEAT_BOX}}</p>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820">{{S05_CONCL}}</p>
  </section>

  <!-- 06 — DO THEY NEED THEM -->
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6">
    <div style="max-width:840px;margin:0 auto;padding:60px 40px 56px">
      <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">{{S06_HEAD}}</h2>
      <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.6;color:#2B2820;margin-bottom:30px;text-wrap:pretty">{{S06_LEAD}}</p>
      {{HEAT_GRID}}
      <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.6;color:#2B2820">{{S06_CONCL}}</p>
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#5A5547;margin-top:20px;line-height:1.6">{{S06_FOOTNOTE}}</p>
    </div>
  </section>

  <!-- LIVING / TREND -->
  {{TREND}}

  <!-- BOTTOM LINE -->
  <section style="max-width:840px;margin:0 auto;padding:46px 40px 20px">
    <div style="border-top:2px solid #1A1813;border-bottom:2px solid #1A1813;padding:44px 0">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:24px">{{BOTTOM_HEAD}}</div>
      <p style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(26px,3.6vw,46px);line-height:1.22;letter-spacing:-.01em;max-width:26ch">{{BOTTOM_TEXT}}</p>
    </div>
  </section>

  <!-- METHOD / FOOTER -->
  <footer style="background:#1A1813;color:#C9C3B2;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:56px 40px 60px">
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:32px 40px">
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">{{FOOT_OUTCOME_H}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">{{FOOT_OUTCOME_T}}</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">{{FOOT_ID_H}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">{{FOOT_ID_T}}</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">{{FOOT_CAV_H}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">{{FOOT_CAV_T}}</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">{{FOOT_REPRO_H}}</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">{{FOOT_REPRO_T}}</p>
          <a href="{{PAGES_URL}}" class="src" style="font-size:13px;display:inline-block;margin-top:12px">{{FOOT_REPRO_LINK}}</a>
        </div>
      </div>
      <div style="height:1px;background:rgba(255,255,255,.14);margin:40px 0 24px"></div>
      {{LANG_TOGGLE}}
      <div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em;color:#7E776A">
        <span>{{FOOT_STAMP1}}</span>
        <span>{{FOOT_STAMP2}}</span>
      </div>
    </div>
  </footer>
</article>

<!-- MATCH MODAL -->
<div id="mb-modal" hidden style="position:fixed;inset:0;z-index:60;display:flex;align-items:center;justify-content:center;background:rgba(26,24,19,.55);padding:20px">
  <div role="dialog" aria-modal="true" aria-labelledby="mb-title" style="background:#FCFAF3;color:#1A1813;width:min(780px,96vw);max-width:96vw;max-height:92vh;overflow-y:auto;overflow-x:hidden;border-radius:4px;box-shadow:0 24px 70px rgba(26,24,19,.4);position:relative;padding:30px 32px 28px">
    <button id="mb-close" aria-label="{{MODAL_CLOSE_ARIA}}" style="position:absolute;top:16px;right:18px;background:none;border:none;cursor:pointer;font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.1em;color:#E5482E"><span aria-hidden="true">{{MODAL_CLOSE}}</span></button>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:10px">{{MODAL_KICKER}}</div>
    <h3 id="mb-title" style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(24px,4vw,34px);line-height:1.1;margin-bottom:6px"></h3>
    <div id="mb-sub" style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557;letter-spacing:.06em;margin-bottom:18px"></div>
    <div id="mb-chart" style="position:relative;width:100%;overflow:hidden;border-radius:3px"></div>
    <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:12px;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.05em;color:#5A5547">
      <span style="display:flex;align-items:center;gap:7px"><span id="mb-sw-home" style="width:16px;height:9px;background:#9CC4E0;display:inline-block;border-radius:1px;flex:none"></span><span><b id="mb-leg-home" style="font-weight:600;color:#3E5E78">{{MODAL_HOME}}</b> {{MODAL_ONTOP}}</span></span>
      <span style="display:flex;align-items:center;gap:7px"><span id="mb-sw-away" style="width:16px;height:9px;background:#EBC09A;display:inline-block;border-radius:1px;flex:none"></span><span><b id="mb-leg-away" style="font-weight:600;color:#9A6A3A">{{MODAL_AWAY}}</b> {{MODAL_ONTOP}}</span></span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:0;height:13px;border-left:2px dashed #3E88C7;display:inline-block"></span>{{LEG_HYDRATION}}</span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:0;height:13px;border-left:2px dotted #7A5CC0;display:inline-block"></span>{{LEG_VAR}}</span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:0;height:13px;border-left:2px dashed #E08A4B;display:inline-block"></span>{{LEG_INJURY}}</span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:11px;height:11px;border-radius:50%;background:#6E90AE;display:inline-block;border:1.5px solid #FCFAF3;box-shadow:0 0 0 1px #CFC6B0;flex:none"></span>{{LEG_GOAL}}</span>
    </div>
    <p id="mb-explain" style="font-family:'Newsreader',serif;font-size:18px;line-height:1.55;color:#2B2820;margin-top:20px"></p>
    <details id="mb-table"></details>
    <style>
     .mb-seg{display:inline-flex;border:1px solid #D2CAB6;border-radius:3px;overflow:hidden}
     .mb-seg button{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.09em;padding:6px 10px;background:#F4F0E5;color:#8A8268;border:none;border-left:1px solid #E2DBCA;cursor:pointer}
     .mb-seg button:first-child{border-left:none}
     .mb-seg button.on{background:#1A1813;color:#EFEBDF}
     .mb-lbl{font-family:'IBM Plex Mono',monospace;font-size:9.5px;letter-spacing:.12em;color:#5A5547;margin-right:6px}
     #mb-share{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.07em;padding:7px 15px;background:#E5482E;color:#fff;border:none;border-radius:3px;cursor:pointer;font-weight:600;margin-left:auto}
     #mb-share:disabled{opacity:.55;cursor:default}
    </style>
    <div style="display:flex;flex-wrap:wrap;gap:12px 14px;align-items:center;margin-top:18px;padding-top:15px;border-top:1px solid #E2DBCA">
      <span class="mb-lbl">{{CTL_COLOURS}}</span><div class="mb-seg" data-group="palette"><button data-val="editorial" class="on">{{CTL_EDITORIAL}}</button><button data-val="kits">{{CTL_KITS}}</button></div>
      <span class="mb-lbl">{{CTL_MODE}}</span><div class="mb-seg" data-group="mode"><button data-val="light" class="on">{{CTL_LIGHT}}</button><button data-val="dark">{{CTL_DARK}}</button></div>
      <button id="mb-share">{{CTL_SHARE}}</button>
    </div>
    <p style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.04em;color:#5A5547;margin-top:12px">{{MODAL_CHARTNOTE}}</p>
  </div>
</div>

<script>
(function(){  // data-freshness: reveal the banner if the committed snapshot is > ~36h old at view time
  var iso="{{SNAPSHOT_ISO}}"; if(!iso) return;
  var ageH=(Date.now() - new Date(iso+"T12:00:00Z").getTime())/3.6e6;
  if(ageH>36){ var b=document.getElementById('freshness'); if(b) b.hidden=false; }
})();
(function(){  // match-grid stage tabs (All / Group / Knockout) + mobile short-scroll
  var tabs=document.querySelectorAll('.mb-tab');
  var mq=window.matchMedia('(max-width:700px)');
  function apply(initial){
    var act='all';
    tabs.forEach(function(t){ if(t.classList.contains('on')) act=t.getAttribute('data-filter'); });
    var vis=[];
    document.querySelectorAll('details.grp').forEach(function(d){
      var show=(act==='all'||act===d.getAttribute('data-stage'));
      d.style.display=show?'':'none'; if(show) vis.push(d);
    });
    // Set the open/closed state only on first load (mobile: only the first group open). On tab
    // clicks we just change visibility, leaving each group as the user left it.
    if(initial){ vis.forEach(function(d,i){ d.open = mq.matches ? (i===0) : true; }); }
  }
  tabs.forEach(function(t){ t.addEventListener('click', function(){
    tabs.forEach(function(x){ var on=(x===t); x.classList.toggle('on',on); x.setAttribute('aria-pressed', on?'true':'false'); });
    apply(false);
  }); });
  apply(true);
})();
(function(){  // plain-language info tooltips: hover (desktop) / tap (mobile) / Enter; Esc or click-away to close
  var pop=document.createElement('div'); pop.id='tip-pop'; pop.setAttribute('role','tooltip');
  document.body.appendChild(pop); var cur=null;
  var canHover=window.matchMedia && window.matchMedia('(hover:hover)').matches;
  function show(b){
    pop.textContent=b.getAttribute('data-tip')||''; pop.classList.add('on');
    var r=b.getBoundingClientRect(), pw=pop.offsetWidth, ph=pop.offsetHeight, m=8;
    var left=window.scrollX+r.left+r.width/2-pw/2;
    left=Math.max(m, Math.min(window.scrollX+document.documentElement.clientWidth-pw-m, left));
    var top=window.scrollY+r.top-ph-9;
    if(top<window.scrollY+m){ top=window.scrollY+r.bottom+9; }  // flip below if no room above
    pop.style.left=left+'px'; pop.style.top=top+'px'; cur=b; b.setAttribute('aria-describedby','tip-pop');
  }
  function hide(){ pop.classList.remove('on'); if(cur) cur.removeAttribute('aria-describedby'); cur=null; }
  document.addEventListener('click', function(ev){
    var b=ev.target.closest && ev.target.closest('.info');
    if(b){ ev.preventDefault(); ev.stopPropagation(); (cur===b)?hide():show(b); return; }
    if(cur && ev.target!==pop) hide();
  });
  document.addEventListener('keydown', function(ev){ if(ev.key==='Escape') hide(); });
  if(canHover){
    document.addEventListener('mouseover', function(ev){ var b=ev.target.closest&&ev.target.closest('.info'); if(b) show(b); });
    document.addEventListener('mouseout', function(ev){ var b=ev.target.closest&&ev.target.closest('.info'); if(b&&cur===b) hide(); });
  }
  window.addEventListener('scroll', function(){ if(cur) hide(); }, {passive:true});
})();
</script>
<script>var T = {{JS_STRINGS}};</script>
<script type="application/json" id="mb-data">{{MB_DATA}}</script>
<script>
(function(){
  var DATA = {}, MARK = {hydration:'#3E88C7', var:'#7A5CC0', injury_huddle:'#E08A4B', injury_no_huddle:'#E08A4B', other:'#9A927E'};
  var DASH = {var:'2 3'};  // VAR is dotted; everything else dashed (set below)
  try { JSON.parse(document.getElementById('mb-data').textContent).forEach(function(m){ DATA[m.id]=m; }); } catch(e){}
  var modal=document.getElementById('mb-modal'), chart=document.getElementById('mb-chart');
  var SVGNS='http://www.w3.org/2000/svg';
  var theme={palette:'editorial', mode:'light'};   // re-render target; share() reads the same
  var cur=null;

  function el(tag, attrs){ var e=document.createElementNS(SVGNS,tag); for(var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function pad2(n){ return (n<10?'0':'')+n; }
  function fmtDate(ts){ if(!ts) return ''; var d=new Date(ts*1000); return pad2(d.getUTCDate())+'/'+pad2(d.getUTCMonth()+1)+'/'+d.getUTCFullYear(); }
  function slug(s){ return (s||'team').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''); }
  function typeName(code){ return (T.types&&T.types[code])||code.replace(/_/g,' '); }

  // resolve {bg,ink,grid,sub,homeFill,awayFill} from the current theme + this match's kit colours
  function resolveTheme(m){
    var dark=theme.mode==='dark';
    var t={ bg: dark?'#1A1813':'#FCFAF3', ink: dark?'#EFEBDF':'#1A1813',
            grid: dark?'rgba(239,235,223,.85)':'#1A1813', sub: dark?'#8E8773':'#9A927E',
            homeFill: dark?'#7FB2D8':'#9CC4E0', awayFill: dark?'#E2B07E':'#EBC09A' };
    if(theme.palette==='kits' && m.colors && m.colors[theme.mode]){
      var c=m.colors[theme.mode];
      if(c.home) t.homeFill=c.home; if(c.away) t.awayFill=c.away;
    }
    return t;
  }

  function chrome(m){
    var t=resolveTheme(m);
    var lh=document.getElementById('mb-leg-home'), la=document.getElementById('mb-leg-away');
    if(lh){ lh.textContent=m.home; } if(la){ la.textContent=m.away; }
    document.getElementById('mb-sw-home').style.background=t.homeFill;
    document.getElementById('mb-sw-away').style.background=t.awayFill;
  }

  function render(m){
    chart.innerHTML='';
    var t=resolveTheme(m);
    chart.style.background=t.bg; chart.style.padding='8px 4px 2px'; chart.style.transition='background .2s';
    var W=720, H=300, pad={l:8,r:8,t:18,b:24};
    var s=m.series; if(!s||!s.length) return;
    var maxMin=s[s.length-1][0], minMin=s[0][0];
    var ymax=1; s.forEach(function(p){ ymax=Math.max(ymax, Math.abs(p[1])); }); ymax*=1.08;
    var pw=W-pad.l-pad.r, ph=H-pad.t-pad.b;
    function X(min){ return pad.l + (min-minMin)/(maxMin-minMin||1)*pw; }
    function Y(v){ return pad.t + (1-(v+ymax)/(2*ymax))*ph; }
    var zeroY=Y(0);
    var svg=el('svg',{viewBox:'0 0 '+W+' '+H, width:'100%', role:'img', style:'display:block;font-family:IBM Plex Mono,monospace'});
    function fillHA(s){ return s.replace(/%H/g,function(){return m.home;}).replace(/%A/g,function(){return m.away;}); }
    var summ=fillHA(T.svgSummary);
    svg.setAttribute('aria-label', summ);
    var ti=el('title',{}); ti.textContent=fillHA(T.svgTitle); svg.appendChild(ti);
    var de=el('desc',{}); de.textContent=summ; svg.appendChild(de);

    var d='M '+X(s[0][0])+' '+zeroY; s.forEach(function(p){ d+=' L '+X(p[0])+' '+Y(p[1]); }); d+=' L '+X(s[s.length-1][0])+' '+zeroY+' Z';
    var defs=el('defs',{});
    defs.appendChild((function(){var c=el('clipPath',{id:'mbUp'});c.appendChild(el('rect',{x:0,y:0,width:W,height:zeroY}));return c;})());
    defs.appendChild((function(){var c=el('clipPath',{id:'mbDn'});c.appendChild(el('rect',{x:0,y:zeroY,width:W,height:H-zeroY}));return c;})());
    svg.appendChild(defs);
    svg.appendChild(el('path',{d:d, fill:t.homeFill, 'clip-path':'url(#mbUp)'}));
    svg.appendChild(el('path',{d:d, fill:t.awayFill, 'clip-path':'url(#mbDn)'}));
    svg.appendChild(el('line',{x1:pad.l,y1:zeroY,x2:W-pad.r,y2:zeroY, stroke:t.grid,'stroke-width':1.1}));

    (m.stoppages||[]).forEach(function(st){
      var x=X(st[0]);
      svg.appendChild(el('line',{x1:x,y1:pad.t,x2:x,y2:H-pad.b, stroke:MARK[st[1]]||'#9A927E','stroke-width':1.3,'stroke-dasharray':DASH[st[1]]||'4 3','stroke-linecap':(DASH[st[1]]?'round':'butt')}));
    });
    // goals: a thin guide in the scoring side's colour, capped by a disc up top (filled = scored,
    // hollow ring = missed penalty). Cleaner than an emoji and still team-coloured.
    (m.goals||[]).forEach(function(g){
      if(g.m<minMin-1 || g.m>maxMin+1) return;
      var x=X(g.m), cy=pad.t-2;
      var gc, gtxt=(g.k==='miss'?T.miss:T.goal)+(g.who?' '+g.who:'')+(g.sc?' '+g.sc:'')+" ("+Math.round(g.m)+"')";
      if(g.k==='miss'){
        svg.appendChild(el('line',{x1:x,y1:cy,x2:x,y2:H-pad.b, stroke:t.sub,'stroke-width':1.2,'stroke-dasharray':'2 3',opacity:.55}));
        gc=el('circle',{cx:x,cy:cy,r:4, fill:t.bg, stroke:t.sub,'stroke-width':1.6});
      } else {
        var col=g.h?t.homeFill:t.awayFill;
        svg.appendChild(el('line',{x1:x,y1:cy,x2:x,y2:H-pad.b, stroke:col,'stroke-width':1.4,opacity:.5}));
        gc=el('circle',{cx:x,cy:cy,r:4.6, fill:col, stroke:t.bg,'stroke-width':1.6});
      }
      var gt=el('title',{}); gt.textContent=gtxt; gc.appendChild(gt); svg.appendChild(gc);
    });
    [0,15,30,45,60,75,90].forEach(function(mm){ if(mm>=minMin-1 && mm<=maxMin+1){ var tx=el('text',{x:X(mm),y:H-7,'text-anchor':'middle','font-size':11,fill:t.sub}); tx.textContent=mm+"'"; svg.appendChild(tx); }});

    var cross=el('line',{y1:pad.t,y2:H-pad.b, stroke:t.grid,'stroke-width':1,opacity:0}); svg.appendChild(cross);
    var dot=el('circle',{r:4, fill:t.ink, stroke:t.bg,'stroke-width':2, opacity:0}); svg.appendChild(dot);
    var tip=document.createElement('div'); tip.style.cssText='position:absolute;pointer-events:none;opacity:0;transform:translate(-50%,-120%);background:'+t.ink+';color:'+t.bg+';font-family:IBM Plex Mono,monospace;font-size:11px;padding:5px 8px;border-radius:3px;white-space:nowrap;transition:opacity .08s';
    chart.appendChild(tip);
    var hit=el('rect',{x:pad.l,y:pad.t,width:pw,height:ph,fill:'transparent',style:'cursor:crosshair'}); svg.appendChild(hit);
    hit.addEventListener('mousemove', function(ev){
      var r=svg.getBoundingClientRect(); var px=(ev.clientX-r.left)/r.width*W;
      var min=minMin+(px-pad.l)/pw*(maxMin-minMin);
      var best=s[0]; for(var i=0;i<s.length;i++){ if(Math.abs(s[i][0]-min)<Math.abs(best[0]-min)) best=s[i]; }
      var x=X(best[0]), y=Y(best[1]);
      cross.setAttribute('x1',x); cross.setAttribute('x2',x); cross.setAttribute('opacity',.5);
      dot.setAttribute('cx',x); dot.setAttribute('cy',y); dot.setAttribute('opacity',1);
      var near=(m.stoppages||[]).filter(function(st){return Math.abs(st[0]-best[0])<1.5;}).map(function(st){return typeName(st[1]);});
      var ng=(m.goals||[]).filter(function(g){return Math.abs(g.m-best[0])<1.6;}).map(function(g){
        return g.k==='miss' ? ('○ '+(g.who||'')+' '+T.penMiss)
          : '● '+(g.who||'')+(g.sc?' '+g.sc:'')+(g.k&&g.k!=='miss'?' ('+g.k+')':''); });
      var extra=near.concat(ng);
      var who=best[1]>=0?(m.home):(m.away);
      tip.innerHTML=Math.round(best[0])+"' · "+(best[1]>0?'+':'')+best[1]+' '+who+(extra.length?' · '+extra.join(' · '):'');
      tip.style.opacity=1;
      var tl=x/W*r.width, hw=tip.offsetWidth/2+4;
      tl=Math.max(hw, Math.min(r.width-hw, tl));
      tip.style.left=tl+'px'; tip.style.top=(y/H*r.height)+'px';
    });
    hit.addEventListener('mouseleave', function(){ cross.setAttribute('opacity',0); dot.setAttribute('opacity',0); tip.style.opacity=0; });
    chart.appendChild(svg);

    // keyboard + screen-reader fallback: a collapsible "Chart data" table of the key moments
    // (every stoppage + goal: minute, event, momentum value, which team was on top).
    var box=document.getElementById('mb-table');
    if(box){
      function esc(x){ return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
      function momAt(min){ var b=s[0]; for(var i=0;i<s.length;i++){ if(Math.abs(s[i][0]-min)<Math.abs(b[0]-min)) b=s[i]; } return b[1]; }
      var moments=[];
      (m.stoppages||[]).forEach(function(st){ moments.push({min:st[0], ev:typeName(st[1])}); });
      (m.goals||[]).forEach(function(g){ moments.push({min:g.m, ev:(g.k==='miss'?T.miss:T.goal)+(g.who?' '+g.who:'')+(g.sc?' '+g.sc:'')}); });
      moments.sort(function(a,b){ return a.min-b.min; });
      var rows='';
      moments.forEach(function(mm){ var v=momAt(mm.min), who=v>=0?m.home:m.away;
        rows+='<tr><td>'+Math.round(mm.min)+"'</td><td>"+esc(mm.ev)+'</td><td>'+(v>0?'+':'')+v+'</td><td>'+esc(who)+'</td></tr>'; });
      if(rows){
        box.hidden=false;
        box.innerHTML='<summary>'+esc(T.dataLabel)+'</summary><table><thead><tr><th>'+esc(T.thMin)+'</th><th>'+esc(T.thEvent)+'</th><th>'+esc(T.thMomentum)+'</th><th>'+esc(T.thLeader)+'</th></tr></thead><tbody>'+rows+'</tbody></table>';
      } else { box.hidden=true; box.innerHTML=''; }
    }
  }

  // ---- shareable themed PNG (canvas) -------------------------------------
  function drawWave(ctx, m, t, box){
    var s=m.series; if(!s||!s.length) return;
    var minMin=s[0][0], maxMin=s[s.length-1][0];
    var ymax=1; s.forEach(function(p){ ymax=Math.max(ymax, Math.abs(p[1])); }); ymax*=1.08;
    function X(min){ return box.x + (min-minMin)/(maxMin-minMin||1)*box.w; }
    function Y(v){ return box.y + (1-(v+ymax)/(2*ymax))*box.h; }
    var zeroY=Y(0);
    function wavePath(){ ctx.beginPath(); ctx.moveTo(X(s[0][0]), zeroY); s.forEach(function(p){ ctx.lineTo(X(p[0]), Y(p[1])); }); ctx.lineTo(X(s[s.length-1][0]), zeroY); ctx.closePath(); }
    ctx.save(); ctx.beginPath(); ctx.rect(box.x, box.y, box.w, zeroY-box.y); ctx.clip(); wavePath(); ctx.fillStyle=t.homeFill; ctx.fill(); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(box.x, zeroY, box.w, box.y+box.h-zeroY); ctx.clip(); wavePath(); ctx.fillStyle=t.awayFill; ctx.fill(); ctx.restore();
    ctx.strokeStyle=t.grid; ctx.lineWidth=1.4; ctx.beginPath(); ctx.moveTo(box.x, zeroY); ctx.lineTo(box.x+box.w, zeroY); ctx.stroke();
    (m.stoppages||[]).forEach(function(st){ var x=X(st[0]); var dot=!!DASH[st[1]]; ctx.strokeStyle=MARK[st[1]]||'#9A927E'; ctx.lineWidth=dot?2.6:2; ctx.lineCap=dot?'round':'butt'; ctx.setLineDash(dot?[0.5,6]:[6,4]); ctx.beginPath(); ctx.moveTo(x, box.y); ctx.lineTo(x, box.y+box.h); ctx.stroke(); ctx.setLineDash([]); ctx.lineCap='butt'; });
    ctx.textAlign='center';
    (m.goals||[]).forEach(function(g){
      if(g.m<minMin-1 || g.m>maxMin+1) return;
      var x=X(g.m), cy=box.y-2;
      if(g.k==='miss'){
        ctx.strokeStyle=t.sub; ctx.lineWidth=1.6; ctx.setLineDash([3,4]); ctx.beginPath(); ctx.moveTo(x,cy); ctx.lineTo(x,box.y+box.h); ctx.stroke(); ctx.setLineDash([]);
        ctx.beginPath(); ctx.arc(x, cy, 6.5, 0, 6.2832); ctx.fillStyle=t.bg; ctx.fill(); ctx.lineWidth=2.2; ctx.strokeStyle=t.sub; ctx.stroke();
      } else {
        var col=(g.h?t.homeFill:t.awayFill);
        ctx.strokeStyle=col; ctx.globalAlpha=.55; ctx.lineWidth=2; ctx.beginPath(); ctx.moveTo(x,cy); ctx.lineTo(x,box.y+box.h); ctx.stroke(); ctx.globalAlpha=1;
        ctx.beginPath(); ctx.arc(x, cy, 7.5, 0, 6.2832); ctx.fillStyle=col; ctx.fill(); ctx.lineWidth=2.4; ctx.strokeStyle=t.bg; ctx.stroke();
        if(g.sc){ ctx.font="600 13px 'IBM Plex Mono'"; ctx.fillStyle=t.ink; ctx.fillText(g.sc, x, box.y-14); }
      }
    });
    ctx.fillStyle=t.sub; ctx.font="22px 'IBM Plex Mono'"; ctx.textAlign='center';
    [0,15,30,45,60,75,90].forEach(function(mm){ if(mm>=minMin-1 && mm<=maxMin+1) ctx.fillText(mm+"'", X(mm), box.y+box.h+30); });
  }

  function shareCard(m){
    var btn=document.getElementById('mb-share'); btn.disabled=true; var lbl=btn.innerHTML; btn.innerHTML=T.rendering;
    (document.fonts?document.fonts.ready:Promise.resolve()).then(function(){
      var t=resolveTheme(m), S=2, Wl=1200, Hl=675;
      var cv=document.createElement('canvas'); cv.width=Wl*S; cv.height=Hl*S;
      var ctx=cv.getContext('2d'); ctx.scale(S,S);
      ctx.fillStyle=t.bg; ctx.fillRect(0,0,Wl,Hl);
      var P=70;
      ctx.textAlign='left';
      ctx.fillStyle='#E5482E'; ctx.font="600 19px 'IBM Plex Mono'"; ctx.fillText(T.shareKicker, P, P+6);
      var score=((m.hs!=null&&m.as!=null)?(' '+m.hs+'–'+m.as+' '):' v ');
      ctx.fillStyle=t.ink; ctx.font="500 50px 'Newsreader'"; ctx.fillText(m.home+score+m.away, P, P+62);
      ctx.fillStyle=t.sub; ctx.font="18px 'IBM Plex Mono'"; var dt=fmtDate(m.ts); ctx.fillText((dt?dt+'  ·  ':'')+(m.series.length)+" "+T.shareMinutes+"  ·  "+((m.stoppages||[]).length)+" "+T.shareStoppages, P, P+96);
      drawWave(ctx, m, t, {x:P, y:200, w:Wl-2*P, h:300});
      // legend row 1: team fills (who's on top)
      ctx.textAlign='left'; var ly=550; ctx.font="600 18px 'IBM Plex Mono'";
      ctx.fillStyle=t.homeFill; ctx.fillRect(P, ly-13, 24, 13); ctx.fillStyle=t.ink; ctx.fillText(m.home+' '+T.onTop, P+34, ly);
      var ox=P+34+ctx.measureText(m.home+' '+T.onTop).width+44;
      ctx.fillStyle=t.awayFill; ctx.fillRect(ox, ly-13, 24, 13); ctx.fillStyle=t.ink; ctx.fillText(m.away+' '+T.onTop, ox+34, ly);
      // legend row 2: stoppage + goal markers
      var my=586, mx=P; ctx.font="600 16px 'IBM Plex Mono'";
      function legLine(label, col, dotted){
        var cy=my-5;
        ctx.strokeStyle=col; ctx.lineWidth=dotted?2.6:2.2; ctx.lineCap=dotted?'round':'butt'; ctx.setLineDash(dotted?[0.5,6]:[6,4]);
        ctx.beginPath(); ctx.moveTo(mx, cy); ctx.lineTo(mx+26, cy); ctx.stroke(); ctx.setLineDash([]); ctx.lineCap='butt';
        ctx.fillStyle=t.ink; ctx.fillText(label, mx+34, my); mx += 34+ctx.measureText(label).width+30;
      }
      legLine(T.legHydration, '#3E88C7', false);
      legLine(T.legVar, '#7A5CC0', true);
      legLine(T.legInjury, '#E08A4B', false);
      ctx.beginPath(); ctx.arc(mx+8, my-6, 7, 0, 6.2832); ctx.fillStyle='#6E90AE'; ctx.fill(); ctx.lineWidth=2; ctx.strokeStyle=t.bg; ctx.stroke();
      ctx.fillStyle=t.ink; ctx.fillText(T.legGoal, mx+24, my);
      // footer
      ctx.strokeStyle=t.grid; ctx.globalAlpha=.3; ctx.lineWidth=1.5; ctx.beginPath(); ctx.moveTo(P, Hl-66); ctx.lineTo(Wl-P, Hl-66); ctx.stroke(); ctx.globalAlpha=1;
      ctx.textAlign='left'; ctx.fillStyle=t.sub; ctx.font="16px 'IBM Plex Mono'"; ctx.fillText(T.shareFoot, P, Hl-36);
      ctx.textAlign='right'; ctx.fillStyle=t.ink; ctx.fillText("valternunez.github.io/wc2026-momentum", Wl-P, Hl-36);
      cv.toBlob(function(blob){
        btn.disabled=false; btn.innerHTML=lbl;
        if(!blob) return;
        var fname='momentum-'+slug(m.home)+'-'+slug(m.away)+'.png';
        try{ var file=new File([blob], fname, {type:'image/png'});
          var navTitle=T.shareNavTitle.replace(/%H/g,function(){return m.home;}).replace(/%A/g,function(){return m.away;});
          if(navigator.canShare && navigator.canShare({files:[file]})){ navigator.share({files:[file], title:navTitle}).catch(function(e){ if(e&&e.name==='AbortError') return; dl(blob,fname); }); return; }
        }catch(e){}
        dl(blob,fname);
      }, 'image/png');
    });
  }
  function dl(blob, fname){ var a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=fname; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function(){URL.revokeObjectURL(a.href);}, 4000); }

  var lastFocus=null, pageRoot=document.querySelector('article');
  function open(id){
    var m=DATA[id]; if(!m) return; cur=m;
    lastFocus=document.activeElement;   // remember trigger to restore focus on close
    var sc=(m.hs!=null&&m.as!=null)?(m.hs+'–'+m.as):'';
    document.getElementById('mb-title').textContent=m.home+(sc?' '+sc+' ':' v ')+m.away;
    var dt=fmtDate(m.ts);
    document.getElementById('mb-sub').textContent=(dt?dt+' · ':'')+(m.series.length)+' '+T.minutesTracked+' · '+(m.stoppages?m.stoppages.length:0)+' '+T.stoppagesDetected;
    document.getElementById('mb-explain').textContent=m.explain||'';
    var sb=document.getElementById('mb-share'); if(sb){ sb.disabled=false; sb.innerHTML=T.shareBtn; }   // reset any stuck RENDERING… state
    chrome(m); render(m); modal.hidden=false; document.body.style.overflow='hidden';
    if(pageRoot) pageRoot.inert=true;   // hide the backgrounded page from AT/tab order
    var c=document.getElementById('mb-close'); if(c) c.focus();   // move focus into the dialog
  }
  function close(){
    modal.hidden=true; document.body.style.overflow='';
    if(pageRoot) pageRoot.inert=false;
    if(lastFocus && lastFocus.focus){ lastFocus.focus(); }   // restore focus to the trigger
  }
  function trapTab(ev){   // keep Tab focus inside the open dialog
    if(modal.hidden || ev.key!=='Tab') return;
    var f=Array.prototype.filter.call(
      modal.querySelectorAll('button, [href], [tabindex]:not([tabindex="-1"])'),
      function(e){ return !e.disabled && e.offsetParent!==null; });
    if(!f.length) return;
    var first=f[0], last=f[f.length-1];
    if(ev.shiftKey && document.activeElement===first){ ev.preventDefault(); last.focus(); }
    else if(!ev.shiftKey && document.activeElement===last){ ev.preventDefault(); first.focus(); }
    else if(!modal.contains(document.activeElement)){ ev.preventDefault(); first.focus(); }
  }
  document.addEventListener('keydown', trapTab);

  document.addEventListener('click', function(ev){
    var card=ev.target.closest('[data-mid]'); if(card){ open(card.getAttribute('data-mid')); }
  });
  // (cards/rows are native <button>s, so Enter/Space activation is handled by the browser)
  document.querySelectorAll('.mb-seg').forEach(function(seg){
    seg.addEventListener('click', function(ev){
      var b=ev.target.closest('button'); if(!b) return;
      theme[seg.getAttribute('data-group')]=b.getAttribute('data-val');
      seg.querySelectorAll('button').forEach(function(x){ x.classList.toggle('on', x===b); });
      if(cur){ chrome(cur); render(cur); }
    });
  });
  document.getElementById('mb-share').addEventListener('click', function(){ if(cur) shareCard(cur); });
  document.getElementById('mb-close').addEventListener('click', close);
  modal.addEventListener('click', function(ev){ if(ev.target===modal) close(); });
  document.addEventListener('keydown', function(ev){ if(ev.key==='Escape' && !modal.hidden) close(); });
})();
</script>
</body></html>
"""
