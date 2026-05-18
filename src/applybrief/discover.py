"""Job discovery via JobSpy + LLM ranking.

Strategy:
  1. Run one JobSpy query per target_role across ALL major boards
     (LinkedIn + Indeed + Google + Glassdoor + ZipRecruiter), logged-out.
  2. Dedupe by job URL.
  3. Apply hard filters: comp floor, avoided industries (cheap pre-filter
     on company name + description).
  4. Send a compact snapshot of each surviving job + the candidate's full
     profile context to the LLM scorer. One call, batched.
  5. Sort by fit score, return top N.

Output:
  - Markdown table to ~/.applybrief/discoveries/<date>-<role>.md
  - (Optional) HTML companion at ~/.applybrief/discoveries/<date>-<role>.html
  - Rich table to the terminal (top 15).
"""

from __future__ import annotations

import datetime as dt
import math
import re
from importlib import resources
from pathlib import Path

from . import llm
from .profile import Profile, discoveries_dir


def _safenum(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return f


def _safestr(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    s = str(v)
    if s.lower() == "nan":
        return ""
    return s


def _slugify(s: str, *, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:max_len] or "search"


DEFAULT_SITES = ["linkedin", "indeed", "google", "glassdoor", "zip_recruiter"]


def _run_jobspy(role, location, hours_old, results_per_site, sites):
    from jobspy import scrape_jobs  # type: ignore

    try:
        df = scrape_jobs(
            site_name=sites,
            search_term=role,
            google_search_term=f"{role} jobs near {location} since last week",
            location=location,
            results_wanted=results_per_site,
            hours_old=hours_old,
            country_indeed="USA",
        )
    except Exception:  # noqa: BLE001
        return []

    rows: list[dict] = []
    if df is None or not len(df):
        return rows
    for _, r in df.iterrows():
        rows.append({
            "site": _safestr(r.get("site", "")),
            "title": _safestr(r.get("title", "")),
            "company": _safestr(r.get("company", "")),
            "location": _safestr(r.get("location", "")),
            "date_posted": _safestr(r.get("date_posted", "")),
            "url": _safestr(r.get("job_url", "")),
            "description": _safestr(r.get("description", ""))[:1500],
            "salary_min": _safenum(r.get("min_amount")),
            "salary_max": _safenum(r.get("max_amount")),
            "is_remote": bool(r.get("is_remote", False)),
        })
    return rows


def _dedupe(rows):
    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        key = r["url"] or f"{r['company']}|{r['title']}|{r['location']}"
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _hard_filter(rows, profile):
    out: list[dict] = []
    avoid = {a.lower() for a in profile.industries_avoid}
    floor = profile.comp_floor or 0
    for r in rows:
        if floor and r["salary_max"]:
            try:
                if float(r["salary_max"]) < floor:
                    continue
            except (TypeError, ValueError):
                pass
        if avoid:
            blob = (r["company"] + " " + r["title"] + " " + (r["description"] or "")).lower()
            if any(a in blob for a in avoid):
                continue
        if not r["title"] or not r["company"]:
            continue
        out.append(r)
    return out


def _score_jobs(rows, profile):
    if not rows:
        return rows
    sys_prompt = resources.files("applybrief.prompts").joinpath("job_scorer.md").read_text()
    job_lines: list[str] = []
    for i, r in enumerate(rows, 1):
        salary = ""
        if r.get("salary_min") or r.get("salary_max"):
            mn = f"${int(r['salary_min']):,}" if r.get("salary_min") else "?"
            mx = f"${int(r['salary_max']):,}" if r.get("salary_max") else "?"
            salary = f" · ${mn}–{mx}"
        desc_snippet = (r.get("description") or "")[:400].replace("\n", " ")
        job_lines.append(
            f"id: {i}\ntitle: {r['title']}\ncompany: {r['company']}\n"
            f"location: {r['location']}{salary}\nremote: {r.get('is_remote', False)}\n"
            f"description: {desc_snippet}\n---"
        )
    user_block = (
        f"## Candidate profile\n\n{profile.context_block()}\n\n"
        f"## Jobs to score ({len(rows)} jobs)\n\n" + "\n".join(job_lines)
    )
    try:
        budget = max(2000, min(8000, 80 * len(rows) + 500))
        out = llm.complete(system=sys_prompt, user=user_block, model=profile.llm_model, max_tokens=budget)
    except Exception as e:  # noqa: BLE001
        from rich.console import Console as _C
        _C().print(f"[yellow]Scorer call failed:[/yellow] {e.__class__.__name__}: {e}")
        for r in rows:
            r["fit_score"] = 50
            r["fit_why"] = "(scorer unavailable; ordering by recency)"
        return rows

    parsed = _parse_score_yaml(out)
    score_by_id = {int(s["id"]): s for s in parsed.get("scores", []) if "id" in s}
    if not score_by_id:
        from rich.console import Console as _C
        snippet = out[:300].replace("\n", " ")
        _C().print(
            f"[yellow]Scorer returned an unparseable response.[/yellow] First 300 chars: {snippet}"
        )
    for i, r in enumerate(rows, 1):
        s = score_by_id.get(i, {})
        try:
            r["fit_score"] = int(s.get("score", 50))
        except (TypeError, ValueError):
            r["fit_score"] = 50
        r["fit_why"] = str(s.get("why", "") or "")
    return rows


def _parse_score_yaml(text):
    import yaml as _yaml
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.endswith("```"):
            s = s[: -3].rstrip()
    try:
        data = _yaml.safe_load(s)
        return data if isinstance(data, dict) else {}
    except _yaml.YAMLError:
        return {}


def discover(
    profile: Profile,
    *,
    role: str | None = None,
    location: str | None = None,
    hours_old: int = 72,
    results_per_site: int = 20,
    sites: list[str] | None = None,
    skip_scoring: bool = False,
    top_n: int = 50,
    render_html: bool = True,
) -> tuple[Path, list[dict], Path | None]:
    """Run a discovery pass. Returns (markdown_path, rows, html_path_or_None)."""
    sites = sites or list(DEFAULT_SITES)

    if role:
        roles_to_query = [role]
    elif profile.target_roles:
        roles_to_query = profile.target_roles[:4]
    elif profile.current_title:
        roles_to_query = [profile.current_title]
    elif profile.narrative:
        roles_to_query = [profile.narrative.strip().split("\n")[0][:80]]
    else:
        raise ValueError("No role to search. Re-run `applybrief init` or pass --role.")

    if profile.remote == "remote":
        location = location or "Remote, United States"
    else:
        location = location or (profile.locations[0] if profile.locations else "United States")

    all_rows: list[dict] = []
    for q in roles_to_query:
        all_rows.extend(_run_jobspy(q, location, hours_old, results_per_site, sites))

    rows = _dedupe(all_rows)
    rows = _hard_filter(rows, profile)

    if not skip_scoring and rows:
        rows = _score_jobs(rows, profile)
        rows.sort(key=lambda r: r.get("fit_score", 0), reverse=True)
    else:
        rows.sort(key=lambda r: r.get("date_posted", ""), reverse=True)

    rows = rows[:top_n]

    today = dt.date.today().isoformat()
    primary_role = roles_to_query[0]
    md_path = discoveries_dir() / f"{today}-{_slugify(primary_role)}.md"

    lines = [
        f"# Discoveries — {', '.join(roles_to_query)}",
        "",
        f"**Date:** {today}  ",
        f"**Location:** {location}  ",
        f"**Sites:** {', '.join(sites)}  ",
        f"**Hours-old cap:** {hours_old}  ",
        f"**Results:** {len(rows)} (after dedup + filter + score)",
        "",
        "| Fit | Company | Title | Location | Posted | Salary | Site | URL | Why |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        salary = ""
        if r.get("salary_min") or r.get("salary_max"):
            mn = f"${int(r['salary_min']):,}" if r.get("salary_min") else "?"
            mx = f"${int(r['salary_max']):,}" if r.get("salary_max") else "?"
            salary = f"{mn}–{mx}"
        fit = r.get("fit_score", "")
        why = (r.get("fit_why", "") or "").replace("|", "\\|")
        lines.append(
            f"| {fit} | {r['company']} | {r['title']} | {r['location']} | "
            f"{r['date_posted']} | {salary} | {r['site']} | "
            f"[link]({r['url']}) | {why} |"
        )
    md_path.write_text("\n".join(lines))

    html_path: Path | None = None
    if render_html:
        try:
            from . import render
            disc_rows = []
            for r in rows:
                salary = ""
                if r.get("salary_min") or r.get("salary_max"):
                    mn = f"${int(r['salary_min']):,}" if r.get("salary_min") else "?"
                    mx = f"${int(r['salary_max']):,}" if r.get("salary_max") else "?"
                    salary = f"{mn}–{mx}"
                disc_rows.append({
                    "fit": r.get("fit_score", 0),
                    "company": r["company"],
                    "title": r["title"],
                    "location": r["location"],
                    "posted": r["date_posted"],
                    "salary": salary,
                    "site": r["site"],
                    "url": r["url"],
                    "why": r.get("fit_why", "") or "",
                })
            meta = {
                "title": f"Discoveries — {', '.join(roles_to_query)}",
                "role": ", ".join(roles_to_query),
                "date": today,
                "location": location,
                "sites": ", ".join(sites),
                "hours_old": hours_old,
                "version": "0.1.0",
                "md_filename": md_path.name,
            }
            html_path = md_path.with_suffix(".html")
            render.render_discoveries_html(disc_rows, meta, html_path)
        except Exception:  # noqa: BLE001
            html_path = None

    return md_path, rows, html_path
