"""Methodology / full-report page template (method.html + method.es.html).

Same editorial look as the main page but prose-only (no modal, no JS). Section copy lives in
i18n.STRINGS as METHOD_* tokens; data figures resolve through the shared {{TOKEN}} pass in
build_site.build_method_pages(). A print stylesheet flattens the page so the committed PDF
(rendered locally via Playwright, like the OG cards) reads as a clean long-form report.

NOTE: non-raw string — never use backslash-escaped double-quotes (\\") inside; Python would
collapse them and break any inline markup. Use single-quoted CSS/attr values where needed.
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{METHOD_META_TITLE}}</title>
<meta name="description" content="{{METHOD_META_DESC}}">
<link rel="canonical" href="{{METHOD_CANONICAL}}">
<meta name="theme-color" content="#EFEBDF">
<meta name="color-scheme" content="light">
<meta name="darkreader-lock">  <!-- light-only editorial design: tell Dark Reader to defer to our styling -->
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%231A1813'/><circle cx='16' cy='16' r='6' fill='%23E5482E'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{color-scheme:light}   /* light-only design: opt out of mobile browsers' Auto Dark Theme */
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif}
  a{color:inherit}
  ::selection{background:#E5482E;color:#FCFAF3}
  :focus-visible{outline:2px solid #E5482E;outline-offset:2px;border-radius:2px}
  .src{font-family:'IBM Plex Mono',monospace;color:#C03A22;text-decoration:none;border-bottom:1px solid #C03A22}
  code{font-family:'IBM Plex Mono',monospace;font-size:.86em;background:#E4DECC;padding:1px 5px;border-radius:3px}
  .wrap{max-width:820px;margin:0 auto;padding:0 40px}
  .m{border-top:1px solid #DDD6C5;padding:34px 0}
  .m h2{font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:16px}
  .m h3{font-family:'Newsreader',serif;font-weight:600;font-size:21px;color:#1A1813;margin:18px 0 8px}
  .m p{font-family:'Newsreader',serif;font-size:18px;line-height:1.62;color:#2B2820;margin-bottom:14px;max-width:64ch}
  .m ul{margin:2px 0 14px 20px}
  .m li{font-family:'Newsreader',serif;font-size:18px;line-height:1.55;color:#2B2820;margin-bottom:9px;max-width:62ch}
  .m table{border-collapse:collapse;margin:8px 0 16px;font-family:'IBM Plex Mono',monospace;font-size:13.5px}
  .m th,.m td{text-align:right;padding:6px 16px 6px 0;border-bottom:1px solid #E0DAC9;color:#2B2820;white-space:nowrap}
  .m th:first-child,.m td:first-child{text-align:left}
  .m th{color:#5A5547;font-weight:600;letter-spacing:.04em}
  .pdfbtn{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:#EFEBDF;background:#1A1813;padding:11px 18px;border-radius:3px;text-decoration:none;margin-top:26px}
  .pdfbtn:hover{background:#E5482E}
  @media print{
    body{background:#fff}
    .wrap{max-width:none;padding:0 4mm}
    .noprint{display:none!important}
    .m{break-inside:avoid;border-top-color:#CFC8B5}
    .m h2{color:#000}
    a{color:#1A1813;border:none}
    footer{background:#fff!important;color:#5A5547!important;margin-top:18px!important}
    footer *{color:#5A5547!important}
    @page{margin:18mm 16mm}
  }
</style></head>
<body>
<article style="width:100%;min-height:100vh;overflow-x:hidden">

  <header class="wrap" style="padding-top:22px;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap">
    <a href="{{HOME_HREF}}" class="noprint" style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#E5482E;text-decoration:none;border-bottom:1px solid rgba(229,72,46,.4)">{{METHOD_BACK}}</a>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.08em;color:#6B6557">{{LIVE_UPDATED}} {{UPDATED_DATE}}</div>
  </header>
  <div class="wrap" style="margin-top:14px"><div style="height:2px;background:#1A1813"></div></div>

  <section class="wrap" style="padding-top:48px;padding-bottom:14px">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">{{METHOD_KICKER}}</div>
    <h1 style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(40px,6vw,76px);line-height:.98;letter-spacing:-.015em;max-width:16ch">{{METHOD_H1}}</h1>
    <p style="font-family:'Newsreader',serif;font-size:clamp(19px,2.2vw,24px);line-height:1.5;max-width:62ch;margin-top:26px;color:#332F26">{{METHOD_LEDE}}</p>
    <a class="pdfbtn noprint" href="{{METHOD_PDF_HREF}}" download>&#8595;&nbsp;{{METHOD_PDF_LABEL}}</a>
  </section>

  <div class="wrap">
    <section class="m" id="findings">{{METHOD_FINDINGS}}</section>
    <section class="m">{{METHOD_WHAT}}</section>
    <section class="m">{{METHOD_DATA}}</section>
    <section class="m">{{METHOD_PIPE}}</section>
    <section class="m">{{METHOD_BASELINES}}</section>
    <section class="m">{{METHOD_CI}}</section>
    <section class="m" id="heat">{{METHOD_HEAT}}</section>
    <section class="m">{{METHOD_ALT}}</section>
    <section class="m">{{METHOD_LIMITS}}</section>
    <section class="m">{{METHOD_REPRO}}</section>
  </div>

  <footer style="background:#1A1813;color:#9A927E;margin-top:40px">
    <div class="wrap" style="padding-top:40px;padding-bottom:46px">
      <div class="noprint" style="margin:0 0 16px"><a href="{{HOME_HREF}}" class="src" style="font-size:13px">{{METHOD_BACK}}</a></div>
      {{LANG_TOGGLE}}
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em;color:#7E776A;margin-top:4px">{{METHOD_FOOT}}</div>
    </div>
  </footer>

</article>
<script>
(function(){
  var ls=document.querySelectorAll('a[href]');
  for(var i=0;i<ls.length;i++){ var a=ls[i], h=a.getAttribute('href')||'';
    if(h.charAt(0)==='#' || a.classList.contains('same-tab')) continue;   // keep in-page anchors + the lang toggle
    a.setAttribute('target','_blank'); a.setAttribute('rel','noopener noreferrer');
  }
})();
</script>
</body>
</html>"""
