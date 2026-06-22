"""Reuse your real Chrome's Cloudflare clearance for fast curl_cffi scraping.

SofaScore's Cloudflare hard-blocks *automated* browsers (Playwright gets a flat 403
even from a residential IP), but your normal Chrome passes as a human. So instead of
driving a browser, we read the `cf_clearance` cookie your real Chrome already earned
and replay it with curl_cffi.

`cf_clearance` is bound to **IP + User-Agent**, so we (a) send the exact User-Agent of
your installed Chrome and (b) only work from the same machine/IP that browsed the site.
It's also **host-scoped**: `api.sofascore.com` needs its own clearance, which Chrome
sets only when the app calls the API — i.e. you must open a **match page** (not just the
homepage) once before scraping. Clearance lasts while your home IP is stable; re-browse
if it expires.

LOCAL ONLY (reads your Chrome cookie store); never used in CI.
"""

from __future__ import annotations

import sys
from contextlib import suppress

_FALLBACK_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)


def chrome_user_agent() -> str:
    """Best-effort exact UA of the installed Chrome (cf_clearance is UA-bound).

    Reads the Chrome version from the Windows registry and builds the modern
    reduced UA string. Falls back to a recent UA if the registry isn't readable.
    """
    if sys.platform.startswith("win"):
        with suppress(Exception):
            import winreg

            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                with suppress(Exception):
                    k = winreg.OpenKey(hive, r"Software\Google\Chrome\BLBeacon")
                    version, _ = winreg.QueryValueEx(k, "version")
                    major = version.split(".")[0]
                    return (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        f"(KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
                    )
    return _FALLBACK_UA


def read_sofascore_cookies(browser: str = "chrome") -> dict[str, str]:
    """Read cookies for sofascore.com (all subdomains) from the local browser."""
    import browser_cookie3 as bc3

    loader = getattr(bc3, browser, bc3.chrome)
    jar = loader(domain_name="sofascore.com")
    return {c.name: c.value for c in jar}


def has_clearance(cookies: dict[str, str]) -> bool:
    return "cf_clearance" in cookies


def make_cookie_client(*, browser: str = "chrome", impersonate: str = "chrome131"):
    """Return a curl_cffi Session preloaded with your Chrome's SofaScore cookies.

    Raises a clear, actionable error if no `cf_clearance` is present (you need to
    open a SofaScore match page in Chrome first). The returned session exposes the
    same `.get()` interface `sofascore._get_json` expects.
    """
    from curl_cffi import requests as creq

    cookies = read_sofascore_cookies(browser)
    if not has_clearance(cookies):
        raise RuntimeError(
            "No 'cf_clearance' cookie found for sofascore.com in your "
            f"{browser} profile. Open a MATCH page on https://www.sofascore.com/ in "
            f"{browser} (so the site calls api.sofascore.com and sets clearance), then retry."
        )

    ua = chrome_user_agent()
    sess = creq.Session(impersonate=impersonate)
    sess.headers.update(
        {
            "User-Agent": ua,  # MUST match the Chrome that earned cf_clearance
            "Accept": "application/json",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    for name, value in cookies.items():
        sess.cookies.set(name, value, domain=".sofascore.com")
    return sess
