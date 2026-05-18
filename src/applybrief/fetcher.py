"""Fetch a JD page and reduce it to clean Markdown.

We intentionally do NOT use a headless browser. For 80% of JDs
(Greenhouse, Lever, Ashby, company career pages) plain httpx is fine.
LinkedIn / Indeed job URLs require auth and are handled separately
via the linkedin-mcp dependency (v0.1+). For now, those return a
friendly "paste JD text instead" hint.
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from markdownify import markdownify

UNSUPPORTED_HOSTS = {
    "www.linkedin.com",
    "linkedin.com",
    "www.indeed.com",
    "indeed.com",
    "www.glassdoor.com",
    "glassdoor.com",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class UnsupportedHostError(Exception):
    """Raised when a JD URL is on a host we don't scrape (LinkedIn, etc.)."""


def fetch_jd_markdown(url: str, *, timeout: float = 15.0) -> str:
    """Fetch a JD URL, return its main content as Markdown."""
    host = urlparse(url).hostname or ""
    if host in UNSUPPORTED_HOSTS:
        raise UnsupportedHostError(
            f"{host} requires authenticated scraping. "
            "Paste the JD text into a file and pass --jd-file <path> instead."
        )

    headers = {"User-Agent": USER_AGENT}
    response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    md = markdownify(response.text, heading_style="ATX", strip=["script", "style"])
    # Collapse runs of blank lines that markdownify leaves behind.
    lines = [line.rstrip() for line in md.splitlines()]
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 1:
                out.append("")
        else:
            blank_run = 0
            out.append(line)
    return "\n".join(out).strip()
