"""Editorial report template + prose (editable copy, separated from data).

The full page is a `{{TOKEN}}`-templated HTML string based on the supplied design
(`WC2026 Momentum Editorial Design`). `build_site.py` computes the token values from
the live committed data and substitutes them (plain str.replace, so the CSS braces in
the <style> block are safe).

Editorial integrity:
- All three pundit quotes are real and sourced (links inline).
- Claims are kept to what the stats support: the *descriptive* ordering is real; the
  causal "huddle" reading is flagged as suggestive, not yet significant.
- Source of truth: FotMob per-minute momentum + ESPN commentary (not SofaScore).
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Do hydration breaks really kill momentum? — WC2026 Stoppage Momentum</title>
<meta name="description" content="Do FIFA's mandatory hydration breaks shift in-match momentum at the 2026 World Cup? A living, data-driven analysis — and a surprising answer.">
<link rel="canonical" href="https://valternunez.github.io/wc2026-momentum/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="WC2026 Stoppage Momentum">
<meta property="og:title" content="Do hydration breaks really kill momentum?">
<meta property="og:description" content="FIFA made hydration breaks mandatory at the 2026 World Cup. The team on top drops ~24 momentum points after one — but a tournament with no breaks shows the same drop. A living, data-driven analysis.">
<meta property="og:url" content="https://valternunez.github.io/wc2026-momentum/">
<meta property="og:image" content="https://valternunez.github.io/wc2026-momentum/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Do hydration breaks really kill momentum? -24 after a break vs -23 with no break.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Do hydration breaks really kill momentum?">
<meta name="twitter:description" content="The team on top drops ~24 momentum points after a hydration break — but a no-breaks tournament shows the same drop. It's regression to the mean.">
<meta name="twitter:image" content="https://valternunez.github.io/wc2026-momentum/og.png">
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
  @keyframes livepulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.78)}}
  .mb-card{transition:transform .14s ease, box-shadow .14s ease}
  .mb-card:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(26,24,19,.10)}
  .src{font-family:'IBM Plex Mono',monospace;color:#E5482E;text-decoration:none;border-bottom:1px solid rgba(229,72,46,.4)}
</style></head>
<body>
<article style="background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif;width:100%;min-height:100vh;overflow-x:hidden">

  <!-- MASTHEAD -->
  <header style="max-width:840px;margin:0 auto;padding:22px 40px 0;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#1A1813;font-weight:600">WC2026 · Stoppage Momentum Study</div>
    <div style="display:flex;align-items:center;gap:9px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:#6B6557">
      <span style="width:8px;height:8px;border-radius:50%;background:#E5482E;display:inline-block;animation:livepulse 1.8s ease-in-out infinite"></span>
      LIVE · UPDATED {{UPDATED_DATE}}
    </div>
  </header>
  <div style="max-width:840px;margin:14px auto 0;padding:0 40px"><div style="height:2px;background:#1A1813"></div></div>

  <!-- HERO -->
  <section style="max-width:840px;margin:0 auto;padding:56px 40px 30px">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:26px">The Hydration-Break Experiment</div>
    <h1 style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(46px,7.4vw,104px);line-height:.95;letter-spacing:-.015em;max-width:15ch;text-wrap:balance">Do hydration breaks really kill momentum?</h1>
    <p style="font-family:'Newsreader',serif;font-size:clamp(20px,2.4vw,28px);line-height:1.45;max-width:760px;margin-top:30px;color:#332F26;text-wrap:pretty">FIFA made in-match hydration breaks mandatory at the 2026 World Cup. Coaches and pundits call them momentum killers. With {{N_MATCHES}} matches in, the data is starting to agree — though maybe not for the reason you'd think.</p>
    <div style="display:flex;gap:28px;flex-wrap:wrap;margin-top:34px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:#6B6557">
      <span>BY THE WC2026 MOMENTUM PROJECT</span>
      <span>{{N_MATCHES}} MATCHES · {{N_STOPPAGES}} STOPPAGES · LIVING ANALYSIS</span>
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
        <p style="font-family:'Newsreader',serif;font-size:clamp(21px,2.3vw,29px);line-height:1.4;color:#EFEBDF;max-width:34ch">momentum points — the average swing <em style="font-style:italic;color:#E5C9A0">away</em> from the team on top in the five minutes after a hydration break.</p>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.07em;color:#948D7C;margin-top:18px;line-height:1.75">
          <div>MEAN OF {{HYD_N}} BREAKS WHERE A TEAM HELD THE EDGE</div>
          <div>FOTMOB PER-MINUTE MOMENTUM SCALE</div>
        </div>
      </div>
    </div>
  </section>

  <!-- 01 — THE CLAIM -->
  <section style="max-width:840px;margin:0 auto;padding:64px 40px 18px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">01 — The claim on TV</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">Every match it's the same beat. The referee blows for the mandated break midway through each half, both sides jog to the touchline for three minutes of water and instructions — and not everyone is convinced it belongs there.</p>
    <blockquote style="font-family:'Newsreader',serif;font-style:italic;font-size:clamp(24px,2.9vw,33px);line-height:1.34;color:#1A1813;border-left:3px solid #E5482E;padding:6px 0 6px 28px;margin:34px 0 16px">"Hydration breaks are a bit interesting … every time going to a commercial is a bit — not really that I like it. If it's really hot it would be good to put them in. But you have to look at it in every game, separately."</blockquote>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.13em;color:#6B6557;text-transform:uppercase;padding-left:28px;margin-bottom:34px">Virgil van Dijk · Netherlands captain, after the 2–2 draw with Japan · <a class="src" href="https://www.espn.com/soccer/story/_/id/49071612/virgil-van-dijk-criticises-world-cup-hydration-breaks">ESPN</a></div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820">Van Dijk's gripe is flow and ad breaks. The sharper charge is tactical — and the booth even has a name for it. ITV's Emma Hayes calls them <em style="font-style:italic">momentum breaks</em>: <span style="color:#1A1813">"advantageous for the team losing momentum … when you're on top, you don't want it; when you're losing, you do."</span> <a class="src" href="https://www.espn.com/soccer/story/_/id/48945011/why-there-drinks-breaks-2026-world-cup-fifa-criticised">[ESPN]</a> A free reset for the team under pressure. The question is whether it survives contact with the data.</p>
  </section>

  <!-- 02 — MONEY CHART -->
  <section style="max-width:840px;margin:0 auto;padding:50px 40px 30px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:10px">02 — What every stoppage does</h2>
    <div style="border-left:3px solid #DDD6C5;padding:2px 0 2px 20px;margin:0 0 28px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#948D7C;margin-bottom:8px">What "momentum" means here</div>
      <p style="font-family:'Newsreader',serif;font-size:18px;line-height:1.55;color:#46412F">A per-minute index from <strong style="font-weight:600">FotMob</strong> of which side is on top — built from the flow of attacks, shots and dangerous moves, not the scoreline. Positive means the home team is pressing, negative the away team. We <em style="font-style:italic">read</em> FotMob's number, we don't compute our own; all we do is measure how it moves in the five minutes either side of a stoppage.</p>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.58;color:#2B2820;margin-bottom:40px">For the team on top before a break, here's how much momentum it loses in the next five minutes — by what kind of stoppage interrupted it. Every bar points the same way. The hydration break points furthest.</p>

    <div style="border-top:2px solid #1A1813;padding-top:30px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px;gap:16px;flex-wrap:wrap">
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.14em;color:#6B6557">MEAN MOMENTUM CHANGE FOR THE TEAM ON TOP</span>
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
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#948D7C;margin-top:14px;line-height:1.6">{{INTERVAL_NOTE}}</p>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-top:34px">{{COMPARE_SENTENCE}}</p>
  </section>

  <!-- 03 — MATCH BY MATCH -->
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:60px 40px 56px">
      <div style="margin-bottom:34px">
        <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:18px">03 — Match by match</h2>
        <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.55;color:#2B2820;text-wrap:pretty">The aggregate is built from these — every match so far, grouped by stage. The wave rises when the <strong style="font-weight:600">home</strong> side is on top, drops when the <strong style="font-weight:600">away</strong> side takes over, and dashed lines mark detected stoppages. <span style="color:#6B6557">Click any match for the full interactive chart.</span></p>
      </div>
      <div style="display:flex;gap:26px;flex-wrap:wrap;align-items:center;margin-bottom:28px;font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.06em;color:#5A5547">
        <span style="display:flex;align-items:center;gap:8px"><span style="width:18px;height:10px;background:#9CC4E0;display:inline-block;border-radius:1px"></span>HOME ON TOP</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:18px;height:10px;background:#EBC09A;display:inline-block;border-radius:1px"></span>AWAY ON TOP</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #3E88C7;display:inline-block"></span>HYDRATION</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #2E8B57;display:inline-block"></span>VAR</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #E08A4B;display:inline-block"></span>INJURY</span>
      </div>
      {{MATCH_CARDS}}
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#948D7C;margin-top:24px;line-height:1.6">Per-minute momentum rendered from FotMob (derived analysis only — raw payloads not redistributed). One panel per scraped match; stoppage markers from the reconciled FotMob + ESPN commentary feed.</p>
    </div>
  </section>

  <!-- 04 — MECHANISM -->
  <section style="background:#1A1813;color:#EFEBDF">
    <div style="max-width:840px;margin:0 auto;padding:62px 40px">
      <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:18px">04 — Is it the huddle, not the water?</h2>
      <p style="font-family:'Newsreader',serif;font-size:clamp(22px,2.6vw,30px);line-height:1.42;color:#EFEBDF;margin-bottom:42px;text-wrap:pretty">Line the stoppages up by how much of a coaching window they create, and the momentum swing roughly tracks them. The more a break looks like a timeout, the harder the leading team tends to fall.</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid rgba(255,255,255,.22)">
        <div style="padding:26px 30px 26px 0;border-right:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5482E;line-height:1">{{MECH_HYD}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">Hydration break</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">Three scheduled minutes. Full organised huddle, water, tactical reset.</p>
        </div>
        <div style="padding:26px 0 26px 30px">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_VAR}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">VAR review</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">A long pause, players idle — but no formal touchline instruction.</p>
        </div>
        <div style="padding:26px 30px 26px 0;border-right:1px solid rgba(255,255,255,.14);border-top:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_IH}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">Injury · with huddle</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">Unscheduled, but long enough for a coach to gather the side.</p>
        </div>
        <div style="padding:26px 0 26px 30px;border-top:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_INH}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">Injury · no huddle</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">Quick stoppage, play resumes before anyone regroups.</p>
        </div>
      </div>
      <p style="font-family:'Newsreader',serif;font-size:20px;line-height:1.6;color:#D8D2C2;margin-top:34px">If a water break were only about <em style="font-style:italic">rest</em>, an equally long VAR pause should match it. So far it doesn't quite — which points at the <strong style="font-weight:600;color:#EFEBDF">coaching window</strong> a break creates. Belgium's Rudi Garcia put it plainly: <span style="color:#EFEBDF">"for me, it's a coaching break more than a cooling break."</span> <a class="src" href="https://www.aljazeera.com/sports/2026/6/20/hydration-break-boos-how-fifa-united-players-fans-coaches-at-world-cup">[Al Jazeera]</a> But read it carefully: once we control for pre-break momentum and pit hydration against a duration-matched VAR, the gap is <strong style="font-weight:600;color:#EFEBDF">not yet statistically distinguishable</strong>. The ordering is suggestive — not a verdict.</p>
    </div>
  </section>

  <!-- 05 — THE CATCH -->
  <section style="max-width:840px;margin:0 auto;padding:64px 40px 18px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">05 — The catch worth stating out loud</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">A team that just had a blazing five minutes tends to cool off <em style="font-style:italic">anyway</em> — break or no break. That's regression to the mean, and it's the single biggest threat to reading too much into the bars above.</p>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">So run the same test on two tournaments with no mandated breaks — measured on the <em style="font-style:italic">same</em> FotMob scale — at the fake 22′/67′ marks. Both show the team on top sliding anyway. And the closest comparison, last summer's Club World Cup in the same US heat, lands almost exactly on the 2026 figure. Most of that headline −24 is regression to the mean, not the water bottle.</p>
    <div style="background:#1A1813;color:#EFEBDF;padding:30px 32px;margin:30px 0;border-radius:2px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.16em;color:#E5C9A0;margin-bottom:18px">NO MANDATED BREAK · SAME FOTMOB SCALE AS THE −24</div>
      <div style="display:flex;gap:48px;flex-wrap:wrap">
        <div>
          <span style="font-family:'Newsreader',serif;font-size:46px;font-weight:500;color:#EFEBDF">{{CWC_MEAN}}</span>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:14px;margin-top:4px;color:#EFEBDF">2025 Club World Cup</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:#948D7C;margin-top:4px;line-height:1.6">{{CWC_CI}}<br>{{CWC_N}} · same US summer</div>
        </div>
        <div>
          <span style="font-family:'Newsreader',serif;font-size:46px;font-weight:500;color:#E5C9A0">{{WC22F_MEAN}}</span>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:14px;margin-top:4px;color:#EFEBDF">2022 World Cup</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:#948D7C;margin-top:4px;line-height:1.6">{{WC22F_CI}}<br>{{WC22F_N}} · cooler Qatar winter</div>
        </div>
      </div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#7E776A;margin-top:18px;line-height:1.6">Both at the 22′/67′ marks where no break was taken. (An event-xT cross-check on 2022 agrees the slide is real.)</div>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820">Which is exactly why the model controls for pre-break momentum, clusters its errors by match, and won't print a causal headline until the live sample is big enough. The interaction regression-to-the-mean <em style="font-style:italic">can't</em> explain — a break hitting harder precisely when a team is on top — is the part still being watched.</p>
  </section>

  <!-- 06 — DO THEY NEED THEM -->
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6">
    <div style="max-width:840px;margin:0 auto;padding:60px 40px 56px">
      <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">06 — Did they even need them?</h2>
      <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.6;color:#2B2820;margin-bottom:30px;text-wrap:pretty">If the momentum case against the breaks is thin, the heat case <em style="font-style:italic">for</em> them is thinner than you'd think. FIFA mandates a break in every match — but cooling breaks were designed for genuine heat stress, and most of these games weren't close to it.</p>
      <div style="display:flex;gap:30px;flex-wrap:wrap;border-top:2px solid #1A1813;border-bottom:1px solid #DDD6C5;padding:26px 0;margin-bottom:26px">
        <div style="flex:1 1 150px"><div style="font-family:'Newsreader',serif;font-size:44px;font-weight:500;color:#E5482E;line-height:1">{{HEAT_HOT32}}/{{HEAT_N}}</div><div style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;color:#46412F;margin-top:8px;line-height:1.45">matches reached <strong style="font-weight:600">WBGT 32°C</strong>, the level that traditionally triggers a cooling break</div></div>
        <div style="flex:1 1 150px"><div style="font-family:'Newsreader',serif;font-size:44px;font-weight:500;color:#1A1813;line-height:1">{{HEAT_DOMED}}</div><div style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;color:#46412F;margin-top:8px;line-height:1.45">were played in <strong style="font-weight:600">air-conditioned domes</strong> — climate already controlled</div></div>
        <div style="flex:1 1 150px"><div style="font-family:'Newsreader',serif;font-size:44px;font-weight:500;color:#1A1813;line-height:1">{{HEAT_MEDIAN}}°</div><div style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;color:#46412F;margin-top:8px;line-height:1.45">median match WBGT — short of the <strong style="font-weight:600">28°C</strong> high-risk line ({{HEAT_HOT28}} cleared it)</div></div>
      </div>
      <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.6;color:#2B2820">So most matches got a mandatory three-minute interruption with neither a momentum effect nor a heat reason. The breaks may still be worth it for the handful of genuinely brutal afternoons — but a fixed, every-match rule looks blunt against the weather.</p>
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#948D7C;margin-top:20px;line-height:1.6">WBGT (wet-bulb globe temperature) approximated from Open-Meteo temperature + humidity at each venue and kickoff. Altitude — Mexico City and Guadalajara sit above 1,500 m — shapes fatigue, not hydration need; the signal for a cooling break is heat and humidity.</p>
    </div>
  </section>

  <!-- LIVING / TREND -->
  {{TREND}}

  <!-- BOTTOM LINE -->
  <section style="max-width:840px;margin:0 auto;padding:46px 40px 20px">
    <div style="border-top:2px solid #1A1813;border-bottom:2px solid #1A1813;padding:44px 0">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:24px">The bottom line — so far</div>
      <p style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(26px,3.6vw,46px);line-height:1.22;letter-spacing:-.01em;max-width:26ch">On the surface the momentum killer is real. But a summer of football with no mandated breaks shows the same drop — so most of it is regression to the mean, and any effect of the break itself is small and unproven. The verdict stays open until the final.</p>
    </div>
  </section>

  <!-- METHOD / FOOTER -->
  <footer style="background:#1A1813;color:#C9C3B2;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:56px 40px 60px">
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:32px 40px">
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">OUTCOME</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">FotMob's per-minute momentum index — their model of which side is on top, from the flow of attacks and chances. We read it, we don't compute it. Reframed per team, windowed 5 minutes either side of each stoppage.</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">IDENTIFICATION</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">Duration-matched comparison of hydration vs VAR vs injury stoppages. Stoppages detected from ESPN commentary, not a hardcoded clock.</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">CAVEATS HANDLED</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">Regression to the mean (2022 historical placebo), score-state asymmetry, substitutions at the break, match-clustered confidence intervals.</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">REPRODUCE</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">Daily-updating dataset and live report regenerate from the committed parquet through the July 19 final.</p>
          <a href="{{PAGES_URL}}" class="src" style="font-size:13px;display:inline-block;margin-top:12px">github.com/valternunez/wc2026-momentum ↗</a>
        </div>
      </div>
      <div style="height:1px;background:rgba(255,255,255,.14);margin:40px 0 24px"></div>
      <div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em;color:#7E776A">
        <span>WC2026 STOPPAGE MOMENTUM STUDY · SNAPSHOT {{SNAPSHOT_DATE}}</span>
        <span>LIVING ANALYSIS · NUMBERS COMPUTED FROM THE COMMITTED DATASET</span>
      </div>
    </div>
  </footer>
</article>

<!-- MATCH MODAL -->
<div id="mb-modal" hidden style="position:fixed;inset:0;z-index:60;display:flex;align-items:center;justify-content:center;background:rgba(26,24,19,.55);padding:20px">
  <div role="dialog" aria-modal="true" aria-labelledby="mb-title" style="background:#FCFAF3;color:#1A1813;width:min(780px,96vw);max-width:96vw;max-height:92vh;overflow-y:auto;overflow-x:hidden;border-radius:4px;box-shadow:0 24px 70px rgba(26,24,19,.4);position:relative;padding:30px 32px 28px">
    <button id="mb-close" aria-label="Close" style="position:absolute;top:16px;right:18px;background:none;border:none;cursor:pointer;font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.1em;color:#E5482E">CLOSE ✕</button>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:10px">Match momentum</div>
    <h3 id="mb-title" style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(24px,4vw,34px);line-height:1.1;margin-bottom:6px"></h3>
    <div id="mb-sub" style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557;letter-spacing:.06em;margin-bottom:18px"></div>
    <div id="mb-chart" style="position:relative;width:100%;overflow:hidden;border-radius:3px"></div>
    <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:12px;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.05em;color:#5A5547">
      <span style="display:flex;align-items:center;gap:7px"><span id="mb-sw-home" style="width:16px;height:9px;background:#9CC4E0;display:inline-block;border-radius:1px;flex:none"></span><span><b id="mb-leg-home" style="font-weight:600;color:#3E5E78">Home</b> on top</span></span>
      <span style="display:flex;align-items:center;gap:7px"><span id="mb-sw-away" style="width:16px;height:9px;background:#EBC09A;display:inline-block;border-radius:1px;flex:none"></span><span><b id="mb-leg-away" style="font-weight:600;color:#9A6A3A">Away</b> on top</span></span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:0;height:13px;border-left:2px dashed #3E88C7;display:inline-block"></span>HYDRATION</span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:0;height:13px;border-left:2px dashed #2E8B57;display:inline-block"></span>VAR</span>
      <span style="display:flex;align-items:center;gap:7px"><span style="width:0;height:13px;border-left:2px dashed #E08A4B;display:inline-block"></span>INJURY</span>
    </div>
    <p id="mb-explain" style="font-family:'Newsreader',serif;font-size:18px;line-height:1.55;color:#2B2820;margin-top:20px"></p>
    <style>
     .mb-seg{display:inline-flex;border:1px solid #D2CAB6;border-radius:3px;overflow:hidden}
     .mb-seg button{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.09em;padding:6px 10px;background:#F4F0E5;color:#8A8268;border:none;border-left:1px solid #E2DBCA;cursor:pointer}
     .mb-seg button:first-child{border-left:none}
     .mb-seg button.on{background:#1A1813;color:#EFEBDF}
     .mb-lbl{font-family:'IBM Plex Mono',monospace;font-size:9.5px;letter-spacing:.12em;color:#A89F88;margin-right:6px}
     #mb-share{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.07em;padding:7px 15px;background:#E5482E;color:#fff;border:none;border-radius:3px;cursor:pointer;font-weight:600;margin-left:auto}
     #mb-share:disabled{opacity:.55;cursor:default}
    </style>
    <div style="display:flex;flex-wrap:wrap;gap:12px 14px;align-items:center;margin-top:18px;padding-top:15px;border-top:1px solid #E2DBCA">
      <span class="mb-lbl">COLOURS</span><div class="mb-seg" data-group="palette"><button data-val="editorial" class="on">EDITORIAL</button><button data-val="kits">TEAM KITS</button></div>
      <span class="mb-lbl">MODE</span><div class="mb-seg" data-group="mode"><button data-val="light" class="on">LIGHT</button><button data-val="dark">DARK</button></div>
      <button id="mb-share">&#8595;&nbsp;SHARE IMAGE</button>
    </div>
    <p style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.04em;color:#A89F88;margin-top:12px">Per-minute momentum, FotMob (home-positive). Hover the chart for values.</p>
  </div>
</div>

<script type="application/json" id="mb-data">{{MB_DATA}}</script>
<script>
(function(){
  var DATA = {}, MARK = {hydration:'#3E88C7', var:'#2E8B57', injury_huddle:'#E08A4B', injury_no_huddle:'#E08A4B', other:'#9A927E'};
  try { JSON.parse(document.getElementById('mb-data').textContent).forEach(function(m){ DATA[m.id]=m; }); } catch(e){}
  var modal=document.getElementById('mb-modal'), chart=document.getElementById('mb-chart');
  var SVGNS='http://www.w3.org/2000/svg';
  var theme={palette:'editorial', mode:'light'};   // re-render target; share() reads the same
  var cur=null;

  function el(tag, attrs){ var e=document.createElementNS(SVGNS,tag); for(var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function pad2(n){ return (n<10?'0':'')+n; }
  function fmtDate(ts){ if(!ts) return ''; var d=new Date(ts*1000); return pad2(d.getUTCDate())+'/'+pad2(d.getUTCMonth()+1)+'/'+d.getUTCFullYear(); }
  function slug(s){ return (s||'team').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''); }

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
    var svg=el('svg',{viewBox:'0 0 '+W+' '+H, width:'100%', style:'display:block;font-family:IBM Plex Mono,monospace'});

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
      svg.appendChild(el('line',{x1:x,y1:pad.t,x2:x,y2:H-pad.b, stroke:MARK[st[1]]||'#9A927E','stroke-width':1.3,'stroke-dasharray':'4 3'}));
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
      var near=(m.stoppages||[]).filter(function(st){return Math.abs(st[0]-best[0])<1.5;}).map(function(st){return st[1].replace(/_/g,' ');});
      var who=best[1]>=0?(m.home):(m.away);
      tip.innerHTML=Math.round(best[0])+"' · "+(best[1]>0?'+':'')+best[1]+' '+who+(near.length?' · '+near[0]:'');
      tip.style.opacity=1;
      var tl=x/W*r.width, hw=tip.offsetWidth/2+4;
      tl=Math.max(hw, Math.min(r.width-hw, tl));
      tip.style.left=tl+'px'; tip.style.top=(y/H*r.height)+'px';
    });
    hit.addEventListener('mouseleave', function(){ cross.setAttribute('opacity',0); dot.setAttribute('opacity',0); tip.style.opacity=0; });
    chart.appendChild(svg);
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
    (m.stoppages||[]).forEach(function(st){ var x=X(st[0]); ctx.strokeStyle=MARK[st[1]]||'#9A927E'; ctx.lineWidth=2; ctx.setLineDash([6,4]); ctx.beginPath(); ctx.moveTo(x, box.y); ctx.lineTo(x, box.y+box.h); ctx.stroke(); ctx.setLineDash([]); });
    ctx.fillStyle=t.sub; ctx.font="22px 'IBM Plex Mono'"; ctx.textAlign='center';
    [0,15,30,45,60,75,90].forEach(function(mm){ if(mm>=minMin-1 && mm<=maxMin+1) ctx.fillText(mm+"'", X(mm), box.y+box.h+30); });
  }

  function shareCard(m){
    var btn=document.getElementById('mb-share'); btn.disabled=true; var lbl=btn.innerHTML; btn.innerHTML='RENDERING…';
    (document.fonts?document.fonts.ready:Promise.resolve()).then(function(){
      var t=resolveTheme(m), S=2, Wl=1200, Hl=675;
      var cv=document.createElement('canvas'); cv.width=Wl*S; cv.height=Hl*S;
      var ctx=cv.getContext('2d'); ctx.scale(S,S);
      ctx.fillStyle=t.bg; ctx.fillRect(0,0,Wl,Hl);
      var P=70;
      ctx.textAlign='left';
      ctx.fillStyle='#E5482E'; ctx.font="600 19px 'IBM Plex Mono'"; ctx.fillText('WC2026 · STOPPAGE MOMENTUM', P, P+6);
      var score=(m.hs!=null?(' '+m.hs+'–'+m.as+' '):' v ');
      ctx.fillStyle=t.ink; ctx.font="500 50px 'Newsreader'"; ctx.fillText(m.home+score+m.away, P, P+62);
      ctx.fillStyle=t.sub; ctx.font="18px 'IBM Plex Mono'"; var dt=fmtDate(m.ts); ctx.fillText((dt?dt+'  ·  ':'')+(m.series.length)+" minutes  ·  "+((m.stoppages||[]).length)+" stoppages", P, P+96);
      drawWave(ctx, m, t, {x:P, y:200, w:Wl-2*P, h:300});
      // legend
      ctx.textAlign='left'; var ly=562; ctx.font="600 20px 'IBM Plex Mono'";
      ctx.fillStyle=t.homeFill; ctx.fillRect(P, ly-14, 26, 14); ctx.fillStyle=t.ink; ctx.fillText(m.home+' on top', P+36, ly);
      var ox=P+36+ctx.measureText(m.home+' on top').width+52;
      ctx.fillStyle=t.awayFill; ctx.fillRect(ox, ly-14, 26, 14); ctx.fillStyle=t.ink; ctx.fillText(m.away+' on top', ox+36, ly);
      // footer
      ctx.strokeStyle=t.grid; ctx.globalAlpha=.3; ctx.lineWidth=1.5; ctx.beginPath(); ctx.moveTo(P, Hl-66); ctx.lineTo(Wl-P, Hl-66); ctx.stroke(); ctx.globalAlpha=1;
      ctx.textAlign='left'; ctx.fillStyle=t.sub; ctx.font="16px 'IBM Plex Mono'"; ctx.fillText("FotMob per-minute momentum", P, Hl-36);
      ctx.textAlign='right'; ctx.fillStyle=t.ink; ctx.fillText("valternunez.github.io/wc2026-momentum", Wl-P, Hl-36);
      cv.toBlob(function(blob){
        btn.disabled=false; btn.innerHTML=lbl;
        if(!blob) return;
        var fname='momentum-'+slug(m.home)+'-'+slug(m.away)+'.png';
        try{ var file=new File([blob], fname, {type:'image/png'});
          if(navigator.canShare && navigator.canShare({files:[file]})){ navigator.share({files:[file], title:m.home+' '+m.away+' — momentum'}).catch(function(){dl(blob,fname);}); return; }
        }catch(e){}
        dl(blob,fname);
      }, 'image/png');
    });
  }
  function dl(blob, fname){ var a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=fname; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function(){URL.revokeObjectURL(a.href);}, 4000); }

  function open(id){
    var m=DATA[id]; if(!m) return; cur=m;
    document.getElementById('mb-title').textContent=m.home+' '+(m.hs!=null?m.hs:'')+(m.hs!=null?'–'+m.as:'')+' '+m.away;
    var dt=fmtDate(m.ts);
    document.getElementById('mb-sub').textContent=(dt?dt+' · ':'')+(m.series.length)+' minutes tracked · '+(m.stoppages?m.stoppages.length:0)+' stoppages detected';
    document.getElementById('mb-explain').textContent=m.explain||'';
    chrome(m); render(m); modal.hidden=false; document.body.style.overflow='hidden';
  }
  function close(){ modal.hidden=true; document.body.style.overflow=''; }

  document.addEventListener('click', function(ev){
    var card=ev.target.closest('[data-mid]'); if(card){ open(card.getAttribute('data-mid')); }
  });
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
