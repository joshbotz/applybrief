"""HTML rendering for applybrief briefs and discoveries.

Self-contained single-file HTML output. No build step.
Tailwind via CDN, vanilla JS only. Prints cleanly to PDF.

Public surface:
    render_brief_html(markdown_text, meta, out_path) -> Path
    render_discoveries_html(rows, meta, out_path) -> Path

Both functions write the HTML file and return its path.
"""

from __future__ import annotations

import html
import importlib.resources
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt


# ---------------------------------------------------------------------------
# Section parsing — split a brief markdown into ordered (heading, html) pairs
# ---------------------------------------------------------------------------

# H2 sections we expect in an Apply Brief, in canonical order.
BRIEF_SECTIONS = [
    "Fit & Gaps",
    "Resume Tailoring",
    "Cover Letter",
    "Warm Intros",
    "Warm Outreach",
    "Hiring Manager",
    "Interview Cheat-Sheet",
    "Next Action",
]


def _md() -> MarkdownIt:
    return MarkdownIt("commonmark", {"breaks": False, "html": False}).enable("table")


def _split_sections(markdown_text: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (header_block, [(section_title, section_md), ...]).

    header_block is everything above the first H2.
    """
    lines = markdown_text.splitlines()
    header: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    current_title = ""

    for line in lines:
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                sections.append((current_title, current))
            current_title = m.group(1).strip()
            current = []
            continue
        if current is None:
            header.append(line)
        else:
            current.append(line)
    if current is not None:
        sections.append((current_title, current))

    header_md = "\n".join(header).strip()
    return header_md, [(t, "\n".join(c).strip()) for t, c in sections]


def _parse_header(header_md: str) -> dict[str, str]:
    """Extract role, company, date, source, fit score from header block."""
    out: dict[str, str] = {}
    # H1
    m = re.search(r"^#\s+(.+?)\s*$", header_md, re.M)
    if m:
        title = m.group(1).strip()
        # "Apply Brief — Role @ Company"
        em = re.match(r"^Apply Brief\s*[—-]\s*(.+?)\s*@\s*(.+)$", title)
        if em:
            out["role"] = em.group(1).strip()
            out["company"] = em.group(2).strip()
        else:
            out["title"] = title
    # bold fields
    for key, label in [
        ("date", "Date"),
        ("source", "Source"),
        ("fit_score", "Fit score"),
    ]:
        m = re.search(rf"\*\*{label}:\*\*\s*(.+?)\s*$", header_md, re.M)
        if m:
            out[key] = m.group(1).strip()
    return out


def _fit_color(fit: int | None) -> str:
    if fit is None:
        return "neutral"
    if fit >= 80:
        return "green"
    if fit >= 50:
        return "amber"
    return "red"


def _parse_fit_score(value: str) -> int | None:
    if not value:
        return None
    m = re.search(r"(\d+)", value)
    return int(m.group(1)) if m else None


def _extract_cover_letter_text(section_md: str) -> str:
    """Return plain-text cover letter for clipboard copy. Strips italics-only refusals."""
    # If the section is one italicized refusal block, return empty (no copy button).
    stripped = section_md.strip()
    if stripped.startswith("_") and stripped.endswith("_") and stripped.count("\n\n") <= 1:
        return ""
    # Strip markdown emphasis markers but keep paragraph breaks.
    txt = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
    txt = re.sub(r"\*(.+?)\*", r"\1", txt)
    txt = re.sub(r"_(.+?)_", r"\1", txt)
    return txt.strip()


# ---------------------------------------------------------------------------
# Template environment
# ---------------------------------------------------------------------------


def _env() -> Environment:
    # Templates ship inside the applybrief package.
    try:
        tpl_dir = importlib.resources.files("applybrief").joinpath("templates")
        loader = FileSystemLoader(str(tpl_dir))
    except (ModuleNotFoundError, FileNotFoundError):
        # Standalone mode (testing): look for templates next to this file.
        loader = FileSystemLoader(str(Path(__file__).parent / "templates"))
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["fit_color"] = _fit_color
    return env


# ---------------------------------------------------------------------------
# Public: brief
# ---------------------------------------------------------------------------


def render_brief_html(
    markdown_text: str,
    meta: dict[str, Any],
    out_path: Path,
) -> Path:
    """Render an Apply Brief markdown to a self-contained HTML file."""
    header_md, sections = _split_sections(markdown_text)
    parsed = _parse_header(header_md)

    role = meta.get("role") or parsed.get("role") or parsed.get("title") or "Apply Brief"
    company = meta.get("company") or parsed.get("company") or ""
    fit_raw = meta.get("fit_score")
    if fit_raw is None:
        fit_raw = _parse_fit_score(parsed.get("fit_score", ""))
    try:
        fit_int = int(fit_raw) if fit_raw is not None and fit_raw != "" else None
    except (TypeError, ValueError):
        fit_int = None
    date = meta.get("date") or parsed.get("date") or ""
    source = meta.get("source_url") or parsed.get("source") or ""
    version = meta.get("version", "0.1.0")
    md_filename = meta.get("md_filename", out_path.with_suffix(".md").name)

    md = _md()
    rendered_sections = []
    cover_letter_text = ""
    for title, body in sections:
        body_html = md.render(body) if body else ""
        # Convert markdown checkboxes to real <input type=checkbox>.
        body_html = re.sub(
            r"<li>\s*\[\s*\]\s*",
            '<li class="task"><input type="checkbox" class="mr-2 align-middle"> ',
            body_html,
        )
        body_html = re.sub(
            r"<li>\s*\[x\]\s*",
            '<li class="task"><input type="checkbox" checked class="mr-2 align-middle"> ',
            body_html,
            flags=re.I,
        )
        section_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        is_cover = title.strip().lower().startswith("cover letter")
        if is_cover:
            cover_letter_text = _extract_cover_letter_text(body)
        rendered_sections.append(
            {
                "title": title,
                "id": section_id,
                "html": body_html,
                "is_cover_letter": is_cover,
                "cover_text": cover_letter_text if is_cover else "",
                "is_next_action": title.strip().lower().startswith("next action"),
            }
        )

    env = _env()
    tpl = env.get_template("brief.html.j2")
    html_out = tpl.render(
        role=role,
        company=company,
        fit=fit_int,
        fit_color=_fit_color(fit_int),
        date=date,
        source=source,
        version=version,
        sections=rendered_sections,
        md_filename=md_filename,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Public: discoveries
# ---------------------------------------------------------------------------


def render_discoveries_html(
    rows: list[dict[str, Any]],
    meta: dict[str, Any],
    out_path: Path,
) -> Path:
    """Render a Discoveries report (list of job rows) to a self-contained HTML file.

    Each row may contain keys: fit, company, title, location, posted, salary,
    site, url, why. Missing keys render as empty.
    """
    env = _env()
    tpl = env.get_template("discoveries.html.j2")

    norm_rows = []
    for r in rows:
        try:
            fit = int(r.get("fit", 0) or 0)
        except (TypeError, ValueError):
            fit = 0
        norm_rows.append(
            {
                "fit": fit,
                "fit_color": _fit_color(fit),
                "company": r.get("company", "") or "",
                "title": r.get("title", "") or "",
                "location": r.get("location", "") or "",
                "posted": r.get("posted", "") or "",
                "salary": r.get("salary", "") or "",
                "site": r.get("site", "") or "",
                "url": r.get("url", "") or "",
                "why": r.get("why", "") or "",
            }
        )

    html_out = tpl.render(
        title=meta.get("title", "Discoveries"),
        role=meta.get("role", ""),
        date=meta.get("date", ""),
        location=meta.get("location", ""),
        sites=meta.get("sites", ""),
        hours_old=meta.get("hours_old", ""),
        total=len(norm_rows),
        rows=norm_rows,
        version=meta.get("version", "0.1.0"),
        md_filename=meta.get("md_filename", out_path.with_suffix(".md").name),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Discoveries: parse from markdown table (helper for callers that have md only)
# ---------------------------------------------------------------------------


def parse_discoveries_markdown(markdown_text: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Parse a discoveries markdown file → (meta, rows). Best-effort."""
    meta: dict[str, str] = {}
    m = re.search(r"^#\s+(.+?)\s*$", markdown_text, re.M)
    if m:
        meta["title"] = m.group(1).strip()
        # "Discoveries — Role A, Role B, Role C"
        tm = re.match(r"^Discoveries\s*[—-]\s*(.+)$", meta["title"])
        if tm:
            meta["role"] = tm.group(1).strip()
    for key, label in [
        ("date", "Date"),
        ("location", "Location"),
        ("sites", "Sites"),
        ("hours_old", "Hours-old cap"),
    ]:
        m = re.search(rf"\*\*{label}:\*\*\s*(.+?)\s*$", markdown_text, re.M)
        if m:
            meta[key] = m.group(1).strip()

    rows: list[dict[str, Any]] = []
    in_table = False
    header_cols: list[str] = []
    for line in markdown_text.splitlines():
        if line.startswith("|") and "---" in line:
            in_table = True
            continue
        if line.startswith("| Fit "):
            header_cols = [c.strip().lower() for c in line.strip("|").split("|")]
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5:
                continue
            # Pad to header length.
            while len(cells) < len(header_cols):
                cells.append("")
            row = dict(zip(header_cols, cells))
            # Convert "[link](url)" → url.
            url_cell = row.get("url", "")
            lm = re.search(r"\((https?://[^)]+)\)", url_cell)
            if lm:
                row["url"] = lm.group(1)
            rows.append(row)
        elif in_table and not line.startswith("|"):
            in_table = False

    return meta, rows
