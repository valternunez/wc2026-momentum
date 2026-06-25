"""Reel/TikTok page template (reel.html + reel.es.html) — a ~20s kinetic myth-buster cut.

A standalone, full-bleed 1080x1920 page that auto-plays a timeline on load: hook → a big animated
GRAPH centerpiece (the break momentum wave dips → -N; then a second no-break control wave fades in
and ALSO dips → -M, "regression to the mean") → honest verdict → CTA. Built to be screen-recorded
into a Reel/TikTok (src/viz/social.build_reel_video). All copy lives in i18n.STRINGS as REEL_* tokens
and every number resolves through the shared {{TOKEN}} pass in build_site.build_reel_pages(), so it
traces to data/processed/* like the rest of the site. The two waves are decorative/schematic (no axis
numbers) — the real figures are the data-driven tokens.

NOTE: non-raw string — never use backslash-escaped double-quotes (\\") inside; Python would
collapse them and break the inline JS. Single-quoted JS/CSS/attr values throughout.
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{REEL_META_TITLE}}</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#14110D">
<meta name="color-scheme" content="light">
<meta name="darkreader-lock">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{color-scheme:light}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{height:100%}
  body{background:#14110D;font-family:'IBM Plex Sans',sans-serif;overflow:hidden}
  .stage{position:fixed;inset:0;display:grid;place-items:center}
  .frame{position:relative;width:min(100vw, calc(100vh * 9 / 16));height:min(100vh, calc(100vw * 16 / 9));
         background:#EFEBDF;color:#1A1813;overflow:hidden;container-type:size}
  /* scenes (centered safe band, clear of platform UI top/bottom) */
  .scene{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
         padding:18cqw 9cqw;opacity:0;visibility:hidden}
  .scene.show{opacity:1;visibility:visible}
  .scene.graph{align-items:center;text-align:center}
  .kicker{font-family:'IBM Plex Mono',monospace;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
          font-size:3.3cqw;color:#C03A22}
  .hookline{font-family:'Newsreader',serif;font-weight:500;font-size:13cqw;line-height:1.0;letter-spacing:-.02em;margin-top:5cqw}
  .hookline span{display:block}
  .kill{color:#C03A22;font-style:italic}
  .tag{font-family:'IBM Plex Mono',monospace;font-size:3.6cqw;letter-spacing:.04em;color:#6B6557;margin-top:6cqw}
  .bignum{font-family:'Newsreader',serif;font-weight:500;font-size:40cqw;line-height:1;letter-spacing:-.02em;margin:2cqw 0}
  .bignum.red{color:#C03A22}
  /* graph centerpiece */
  .bigwave{width:100%;height:auto;overflow:visible;margin-bottom:7cqw}
  .bw-band{fill:#78716220}
  .bw-zero{stroke:#B8B19E;stroke-width:1}
  .bw-break{fill:none;stroke:#C03A22;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:100;stroke-dashoffset:100}
  .bw-nb{fill:none;stroke:#9A927E;stroke-width:3.4;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:100;stroke-dashoffset:100;opacity:0}
  .gnums{display:flex;justify-content:center;align-items:flex-end;gap:9cqw}
  .gcol{display:flex;flex-direction:column;align-items:center}
  .gn{font-family:'Newsreader',serif;font-weight:500;font-size:18cqw;line-height:.9;letter-spacing:-.02em}
  .gn.red{color:#C03A22}.gn.ink{color:#1A1813}
  .gl{font-family:'IBM Plex Mono',monospace;font-size:3cqw;letter-spacing:.03em;color:#5A5547;margin-top:2cqw}
  .gline{font-family:'Newsreader',serif;font-size:7cqw;line-height:1.2;color:#1A1813;margin-top:8cqw;max-width:20ch}
  /* verdict */
  .vk{font-family:'IBM Plex Mono',monospace;font-weight:600;letter-spacing:.2em;text-transform:uppercase;font-size:3.4cqw;color:#6B6557}
  .ci{font-family:'IBM Plex Mono',monospace;font-size:3.6cqw;color:#6B6557;margin-top:2cqw}
  .verdict-line{font-family:'Newsreader',serif;font-size:6cqw;line-height:1.25;color:#1A1813;margin-top:5cqw;max-width:20ch}
  /* cta */
  .cta-line{font-family:'Newsreader',serif;font-weight:500;font-size:9cqw;line-height:1.05;margin-top:5cqw}
  .cta-url{font-family:'IBM Plex Mono',monospace;font-size:4cqw;letter-spacing:.02em;color:#C03A22;margin-top:5cqw}
  /* motion */
  @keyframes slamIn{0%{opacity:0;transform:scale(1.5)}62%{opacity:1;transform:scale(.94)}100%{opacity:1;transform:scale(1)}}
  @keyframes riseIn{0%{opacity:0;transform:translateY(4cqw)}100%{opacity:1;transform:translateY(0)}}
  @keyframes wipeIn{0%{clip-path:inset(0 100% 0 0);opacity:.25}100%{clip-path:inset(0 0 0 0);opacity:1}}
  @keyframes drawWave{to{stroke-dashoffset:0}}
  @keyframes fadeIn{to{opacity:1}}
  .a-rise,.a-slam,.b-rise,.b-slam,.b-wipe{opacity:0}
  .scene.show .a-rise{animation:riseIn .5s cubic-bezier(.2,.7,.2,1) both}
  .scene.show .a-slam{animation:slamIn .62s cubic-bezier(.2,.7,.2,1) both}
  .scene.show .bw-break{animation:drawWave 1.3s ease both}
  /* step-2 reveal inside the graph scene (the no-break wave + its number + the punch line) */
  .scene.step2 .bw-nb{animation:drawWave 1.1s ease both, fadeIn .5s ease both}
  .scene.step2 .b-slam{animation:slamIn .62s cubic-bezier(.2,.7,.2,1) both}
  .scene.step2 .b-rise{animation:riseIn .5s cubic-bezier(.2,.7,.2,1) both .1s}
  .scene.step2 .b-wipe{animation:wipeIn .6s ease both .18s}
  .d1{animation-delay:.10s}.d2{animation-delay:.22s}.d3{animation-delay:.36s}.d4{animation-delay:.52s}
  /* graph step-1: let the -N land as the break wave finishes drawing (~1.3s) */
  .g-num{animation-delay:.85s}.g-lbl{animation-delay:1.1s}
  @media (prefers-reduced-motion: reduce){
    .a-rise,.a-slam,.b-rise,.b-slam,.b-wipe{opacity:1}
    .scene.show .a-rise,.scene.show .a-slam,.scene.step2 .b-rise,.scene.step2 .b-slam,.scene.step2 .b-wipe{animation:none}
    .bw-break,.bw-nb{stroke-dashoffset:0}.bw-nb{opacity:1}
  }
</style></head>
<body>
<div class="stage"><div class="frame">

  <!-- 1 — hook -->
  <section class="scene" data-scene="hook">
    <div class="kicker a-rise d1">{{REEL_KICKER}}</div>
    <h1 class="hookline">
      <span class="a-rise d2">{{REEL_HOOK1}}</span>
      <span class="kill a-rise d3">{{REEL_HOOK_KILL}}</span>
      <span class="a-rise d4">{{REEL_HOOK2}}</span>
    </h1>
    <div class="tag a-rise d4">{{REEL_HOOK_TAG}}</div>
  </section>

  <!-- 2 — the graph (hero; stages: break wave + -N, then the no-break wave + -M) -->
  <section class="scene graph" data-scene="graph">
    <svg class="bigwave" viewBox="0 0 320 170" role="presentation">
      <rect class="bw-band" x="150" y="8" width="34" height="154"></rect>
      <line class="bw-zero" x1="8" y1="92" x2="312" y2="92"></line>
      <path class="bw-nb" pathLength="100" d="M8,78 C50,44 92,40 132,54 C172,68 206,86 246,100 C276,110 296,108 312,112"></path>
      <path class="bw-break" pathLength="100" d="M8,92 C44,52 74,42 104,56 C124,64 138,46 150,48 L184,48 C206,90 226,132 256,122 C282,114 298,110 312,112"></path>
    </svg>
    <div class="gnums">
      <div class="gcol"><span class="gn red a-slam g-num">&#8722;{{HERO_DELTA}}</span><span class="gl a-rise g-lbl">{{REEL_PROOF_LABEL}}</span></div>
      <div class="gcol"><span class="gn ink b-slam">&#8722;{{P26_DELTA}}</span><span class="gl b-rise">{{REEL_TWIST_LABEL}}</span></div>
    </div>
    <div class="gline b-wipe">{{REEL_TWIST_LINE}}</div>
  </section>

  <!-- 3 — verdict -->
  <section class="scene" data-scene="verdict">
    <div class="vk a-rise d1">{{REEL_VERDICT_KICKER}}</div>
    <div class="bignum red a-slam d2">{{GAP}}</div>
    <div class="ci a-rise d3">95% CI {{GAP_LO}} &middot;&middot;&middot; {{GAP_HI}}</div>
    <div class="verdict-line a-rise d4">{{REEL_VERDICT}}</div>
  </section>

  <!-- 4 — cta -->
  <section class="scene" data-scene="cta">
    <div class="kicker a-rise d1">{{REEL_KICKER}}</div>
    <div class="cta-line a-rise d2">{{REEL_CTA}}</div>
    <div class="cta-url a-rise d3">{{REEL_CTA_URL}}</div>
  </section>

</div></div>
<script>
(function(){
  var order=['hook','graph','verdict','cta'], scenes={};
  [].forEach.call(document.querySelectorAll('.scene'), function(s){ scenes[s.getAttribute('data-scene')]=s; });
  var schedule=[[0,'hook'],[3500,'graph'],[13000,'verdict'],[17000,'cta']];
  var step2At=7000;   // mid-graph: reveal the no-break wave + its number + the punch line
  var rm=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function show(name){ order.forEach(function(n){ scenes[n].classList.toggle('show', n===name); }); }
  function play(){
    if(rm){ scenes.graph.classList.add('step2'); show('cta'); return; }
    schedule.forEach(function(e){ setTimeout(function(){ show(e[1]); }, e[0]); });
    setTimeout(function(){ if(scenes.graph) scenes.graph.classList.add('step2'); }, step2At);
  }
  // The recorder loads with ?rec and calls __play() to start the timeline at a known instant (so the
  // captured window aligns exactly); a direct browser visit just auto-plays.
  window.__play=play;
  if(location.search.indexOf('rec')===-1){ play(); }
})();
</script>
</body>
</html>"""
