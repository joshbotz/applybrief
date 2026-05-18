"""Apply Brief generation — the hero command.

Flow:
  1. Fetch JD URL → Markdown (fetcher.py)
  2. LLM parse JD → structured Markdown (jd_parser.md)
  3. LLM generate Apply Brief from parsed JD + resume (apply_brief.md)
  4. Write to ~/.applybrief/briefs/<slug>.md
  5. (Optional) Render an HTML companion alongside the .md
  6. Return (md_path, html_path or None)
"""

from __future__ import annotations

import datetime as dt
import re
from importlib import resources
from pathlib import Path

from . import fetcher, llm
from .profile import Profile, briefs_dir


def _load_prompt(name: str) -> str:
    pkg_files = resources.files("applybrief.prompts")
    return pkg_files.joinpath(name).read_text(encoding="utf-8")


def _slugify(text: str, *, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:max_len] or "untitled"


def _parse_jd_meta(parsed_jd: str) -> tuple[str, str]:
    """Pull company + role out of the parsed JD markdown."""
    company = "Unknown"
    role = "Unknown Role"
    current: str | None = None
    for raw_line in parsed_jd.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("### Company"):
            current = "company"
            continue
        if line.startswith("### Role"):
            current = "role"
            continue
        if line.startswith(("#", "-")):
            if line.startswith("#"):
                current = None
            continue
        if current == "company" and company == "Unknown":
            company = line
        elif current == "role" and role == "Unknown Role":
            role = line
    return company, role


def _parse_fit_score(brief_md: str) -> int | None:
    """Extract '**Fit score:** NN/100' from the generated brief."""
    m = re.search(r"\*\*Fit score:\*\*\s*(\d+)", brief_md)
    return int(m.group(1)) if m else None


def generate(
    url: str | None = None,
    *,
    jd_text: str | None = None,
    profile: Profile,
    resume_text: str,
    render_html: bool = True,
) -> tuple[Path, Path | None]:
    """Generate an Apply Brief. Provide either `url` or `jd_text`.

    Returns (markdown_path, html_path).  `html_path` is None when render_html=False
    or when rendering fails (HTML is best-effort; the markdown is canonical).
    """
    if not url and not jd_text:
        raise ValueError("Provide either a JD URL or paste the JD text.")

    if jd_text:
        jd_md = jd_text
        source = "pasted"
    else:
        jd_md = fetcher.fetch_jd_markdown(url)  # type: ignore[arg-type]
        source = url  # type: ignore[assignment]

    parsed_jd = llm.complete(
        system=_load_prompt("jd_parser.md"),
        user=jd_md,
        model=profile.llm_model,
    )

    company, role = _parse_jd_meta(parsed_jd)

    user_block = (
        f"## Parsed JD\n\n{parsed_jd}\n\n"
        f"## Candidate resume\n\n{resume_text or '_(no resume provided)_'}\n\n"
        f"## Candidate context\n\n{profile.context_block()}\n\n"
        f"## Source\n{source}\n\n"
        f"## Today's date\n{dt.date.today().isoformat()}\n"
    )

    brief_md = llm.complete(
        system=_load_prompt("apply_brief.md"),
        user=user_block,
        model=profile.llm_model,
        max_tokens=6000,
    )

    today = dt.date.today().isoformat()
    slug = f"{today}-{_slugify(company)}-{_slugify(role)}"
    md_path = briefs_dir() / f"{slug}.md"
    md_path.write_text(brief_md)

    html_path: Path | None = None
    if render_html:
        try:
            from . import render  # local import — keeps cli startup snappy
            meta = {
                "role": role,
                "company": company,
                "fit_score": _parse_fit_score(brief_md),
                "date": today,
                "source_url": source if source != "pasted" else "",
                "version": "0.1.0",
                "md_filename": md_path.name,
            }
            html_path = md_path.with_suffix(".html")
            render.render_brief_html(brief_md, meta, html_path)
        except Exception:  # noqa: BLE001
            # HTML is best-effort. The .md is the canonical output.
            html_path = None

    return md_path, html_path
