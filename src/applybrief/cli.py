"""applybrief CLI — Typer.

Commands:
  init        one-time conversational onboarding
  apply <url> the hero — generate an Apply Brief from a JD URL
  discover    search for jobs matching your profile
  config      show current profile
  doctor      diagnose env / deps
"""

from __future__ import annotations

import os
import shutil
import sys
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import brief, discover as _discover, fetcher, llm
from .profile import Profile, profile_path, resume_path, applybrief_dir

app = typer.Typer(
    help="applybrief — find roles worth your time. Write the boring parts.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()


# ---------- helpers ----------


def _ensure_profile() -> Profile:
    p = Profile.load()
    if p is None:
        console.print(
            Panel(
                "[bold]Welcome.[/bold] Looks like this is your first run.\n\n"
                "Let's set up your profile (~60 seconds): "
                "[cyan]applybrief init[/cyan]",
                title="applybrief",
                border_style="cyan",
            )
        )
        raise typer.Exit(code=1)
    return p


def _looks_like_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))


def _maybe_open(html_path: Path | None, no_open: bool) -> None:
    """Open the HTML in the default browser unless --no-open or no html was rendered."""
    if no_open or html_path is None:
        return
    try:
        webbrowser.open(html_path.as_uri())
    except Exception:  # noqa: BLE001
        pass


# ---------- root callback (no-arg summary) ----------


def _version_callback(value: bool) -> None:
    if value:
        from . import __version__
        console.print(f"applybrief {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-V",
        callback=_version_callback, is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    if ctx.invoked_subcommand is None:
        _summary()
        raise typer.Exit()


# ---------- main entry: pre-parse for URL auto-route ----------


def main() -> None:
    """Console entry point. Rewrites `applybrief <url>` → `applybrief apply <url>`."""
    if len(sys.argv) >= 2 and _looks_like_url(sys.argv[1]):
        sys.argv.insert(1, "apply")
    app()


def _summary() -> None:
    p = Profile.load()
    if p is None:
        console.print(
            Panel.fit(
                "[bold]applybrief[/bold] — find roles worth your time. Write the boring parts.\n\n"
                "Get started:  [cyan]applybrief init[/cyan]",
                border_style="cyan",
            )
        )
        return

    from .profile import briefs_dir

    n_briefs = len(list(briefs_dir().glob("*.md")))
    console.print(
        Panel.fit(
            f"[bold]applybrief[/bold]\n\n"
            f"Profile:  {p.name or '(unnamed)'} · {p.email or 'no email'}\n"
            f"Targets:  {', '.join(p.target_roles) or '(none set)'}\n"
            f"Model:    {p.llm_model}\n"
            f"Briefs:   {n_briefs} drafted\n\n"
            "Try:  [cyan]applybrief discover[/cyan]  or  [cyan]applybrief <jd-url>[/cyan]",
            border_style="cyan",
        )
    )


# ---------- init ----------


@app.command()
def init(
    resume: Path = typer.Option(
        None, "--resume", "-r", help="Path to your resume (PDF, DOCX, MD, or TXT). Skips the prompt."
    ),
) -> None:
    """One-time conversational onboarding."""
    console.print(
        Panel(
            "[bold]Welcome.[/bold]\n\n"
            "I'll read your resume, then ask 4 short questions about what you want.\n"
            "Write as much or as little as you like — natural language is fine.\n"
            "I'll turn it into a profile you can edit later.\n\n"
            "Your answers stay local. Nothing is sent anywhere except the LLM call\n"
            "that parses what you wrote.",
            title="applybrief init",
            border_style="cyan",
        )
    )

    existing = Profile.load()
    if existing:
        if not Confirm.ask(
            f"\nA profile already exists at {profile_path()}. Overwrite?",
            default=False,
        ):
            console.print("Cancelled.")
            raise typer.Exit()

    p = Profile()

    # If --resume was passed and valid, use it; otherwise prompt.
    if resume is not None:
        src = resume.expanduser()
        if not (src.exists() and src.is_file()):
            console.print(f"[red]Resume not found:[/red] {src}")
            raise typer.Exit(code=1)
    else:
        while True:
            path_str = Prompt.ask("\n[bold]Path to your resume[/bold] (PDF, DOCX, MD, or TXT)")
            src = Path(path_str).expanduser()
            if src.exists() and src.is_file():
                break
            console.print(f"[red]Not found:[/red] {src}. Try again.")

    resume_md = _ingest_resume(src)
    resume_path().parent.mkdir(parents=True, exist_ok=True)
    resume_path().write_text(resume_md)
    console.print(f"[green]✓[/green] Resume parsed.")

    console.print("[dim]Reading your resume for contact info...[/dim]")
    contact = _extract_contact(resume_md, p.llm_model)
    p.name = contact.get("name", "") or ""
    p.email = contact.get("email", "") or ""
    p.phone = contact.get("phone", "") or ""
    p.linkedin_url = contact.get("linkedin_url", "") or ""
    p.location = contact.get("location", "") or ""
    p.current_title = contact.get("current_title", "") or ""
    try:
        p.years_experience = int(contact.get("years_experience", 0) or 0)
    except (TypeError, ValueError):
        p.years_experience = 0

    found_lines = []
    if p.name:
        found_lines.append(f"  Name:     {p.name}")
    if p.email:
        found_lines.append(f"  Email:    {p.email}")
    if p.linkedin_url:
        found_lines.append(f"  LinkedIn: {p.linkedin_url}")
    if p.location:
        found_lines.append(f"  Location: {p.location}")
    if p.current_title:
        found_lines.append(f"  Title:    {p.current_title} ({p.years_experience}y)")
    if found_lines:
        console.print(
            Panel(
                "I pulled this from your resume:\n\n" + "\n".join(found_lines),
                border_style="dim",
            )
        )

    console.print(
        Panel(
            "[bold]Tell me what you want. Use your own words.[/bold]\n\n"
            "Four questions. There's no wrong answer; longer is fine.\n"
            "If you don't know, say 'not sure' and I'll infer from your resume.",
            border_style="cyan",
        )
    )

    p.narrative = Prompt.ask(
        "\n[bold]1. What kind of work are you looking for?[/bold]\n"
        "[dim]   (describe it — role, scope, problems you want to solve, "
        "type of company. Don't worry about job titles.)[/dim]\n"
    )

    p.must_haves = Prompt.ask(
        "\n[bold]2. What do you absolutely need?[/bold]\n"
        "[dim]   (e.g. 'must be remote', 'requires clearance', 'no travel', "
        "minimum salary, healthcare benefits...)[/dim]\n",
        default="",
    )

    p.deal_breakers = Prompt.ask(
        "\n[bold]3. What do you not want?[/bold]\n"
        "[dim]   (e.g. 'no on-call', 'not interested in startups', "
        "'no big banks', 'no relocation'...)[/dim]\n",
        default="",
    )

    p.other_context = Prompt.ask(
        "\n[bold]4. Anything else I should know?[/bold]\n"
        "[dim]   (family situation, career pivot, return-to-work, "
        "what would make you happy)[/dim]\n",
        default="",
    )

    console.print("\n[dim]Parsing what you wrote...[/dim]")
    intent = _extract_intent(resume_md, p, p.llm_model)
    p.target_roles = intent.get("target_roles", []) or []
    p.target_seniority = intent.get("target_seniority", "") or ""
    p.remote = intent.get("remote", "remote") or "remote"
    p.locations = intent.get("locations", []) or []
    try:
        p.comp_floor = int(intent.get("comp_floor", 0) or 0)
    except (TypeError, ValueError):
        p.comp_floor = 0
    p.industries_focus = intent.get("industries_focus", []) or []
    p.industries_avoid = intent.get("industries_avoid", []) or []
    p.clearance = intent.get("clearance", "") or ""
    p.special_circumstances = intent.get("special_circumstances", "") or ""

    summary_lines = [
        f"  Target roles:    {', '.join(p.target_roles) or '(none derived)'}",
        f"  Seniority:       {p.target_seniority or '(unspecified)'}",
        f"  Work mode:       {p.remote}",
    ]
    if p.locations:
        summary_lines.append(f"  Locations:       {', '.join(p.locations)}")
    summary_lines.append(
        f"  Comp floor:      {'$' + format(p.comp_floor, ',') if p.comp_floor else '(unspecified)'}"
    )
    if p.industries_focus:
        summary_lines.append(f"  Industries:      {', '.join(p.industries_focus)}")
    if p.industries_avoid:
        summary_lines.append(f"  Avoid:           {', '.join(p.industries_avoid)}")
    if p.clearance:
        summary_lines.append(f"  Clearance:       {p.clearance}")
    if p.special_circumstances:
        summary_lines.append(f"  Notes:           {p.special_circumstances}")

    console.print(
        Panel(
            "Here's what I understood:\n\n" + "\n".join(summary_lines),
            title="Parsed profile",
            border_style="cyan",
        )
    )

    if not Confirm.ask("\nLooks right? (You can edit profile.yaml later either way)", default=True):
        console.print(
            "[yellow]No problem.[/yellow] Open this file in any editor and adjust:\n"
            f"   {profile_path()}\n"
            "Your free-form answers are preserved under [bold]narrative[/bold], "
            "[bold]must_haves[/bold], [bold]deal_breakers[/bold], [bold]other_context[/bold]."
        )

    console.print(
        Panel(
            "[bold]One last thing — pick the AI model.[/bold]\n\n"
            "  [cyan]1[/cyan]  Anthropic Claude Haiku   — ~$0.001/brief  (recommended)\n"
            "  [cyan]2[/cyan]  Anthropic Claude Sonnet  — ~$0.01/brief   (highest quality)\n"
            "  [cyan]3[/cyan]  Groq Llama 3.1 70B       — free tier      (fastest)\n"
            "  [cyan]4[/cyan]  OpenAI GPT-4o-mini       — ~$0.002/brief\n"
            "  [cyan]5[/cyan]  Ollama (local)           — $0 (slow)\n\n"
            "You need the matching API key in your shell env "
            "(ANTHROPIC_API_KEY, GROQ_API_KEY, OPENAI_API_KEY).",
            border_style="cyan",
        )
    )
    choice = Prompt.ask("Pick", choices=["1", "2", "3", "4", "5"], default="1")
    p.llm_model = {
        "1": "anthropic/claude-haiku-4-5",
        "2": "anthropic/claude-sonnet-4-6",
        "3": "groq/llama-3.1-70b-versatile",
        "4": "openai/gpt-4o-mini",
        "5": "ollama/llama3.1",
    }[choice]

    p.save()
    console.print(
        Panel(
            f"[green bold]✓ Profile saved.[/green bold]\n\n"
            f"Resume:   {resume_path()}\n"
            f"Profile:  {profile_path()}\n"
            f"Model:    {p.llm_model}\n\n"
            "Next steps:\n"
            f"  [cyan]applybrief discover[/cyan]              find jobs matching your profile\n"
            f"  [cyan]applybrief <jd-url>[/cyan]              draft an Apply Brief for a posting\n"
            f"  [cyan]applybrief doctor[/cyan]                check your environment",
            title="You're set",
            border_style="green",
        )
    )


def _extract_contact(resume_md: str, model: str) -> dict:
    from importlib import resources
    sys_prompt = resources.files("applybrief.prompts").joinpath("contact_extractor.md").read_text()
    try:
        out = llm.complete(system=sys_prompt, user=resume_md, model=model, max_tokens=400)
    except Exception as e:  # noqa: BLE001
        console.print(f"[yellow]Couldn't extract contact info ({e.__class__.__name__}). "
                      "I'll skip and you can edit the profile later.[/yellow]")
        return {}
    return _parse_yaml_block(out)


def _extract_intent(resume_md: str, p: Profile, model: str) -> dict:
    from importlib import resources
    sys_prompt = resources.files("applybrief.prompts").joinpath("intent_extractor.md").read_text()
    user_block = (
        f"# Resume\n\n{resume_md}\n\n"
        f"# Question 1 — What kind of work?\n{p.narrative or '(no answer)'}\n\n"
        f"# Question 2 — Must-haves\n{p.must_haves or '(no answer)'}\n\n"
        f"# Question 3 — Won't accept\n{p.deal_breakers or '(no answer)'}\n\n"
        f"# Question 4 — Anything else\n{p.other_context or '(no answer)'}\n"
    )
    try:
        out = llm.complete(system=sys_prompt, user=user_block, model=model, max_tokens=800)
    except Exception as e:  # noqa: BLE001
        console.print(f"[yellow]Couldn't parse intent ({e.__class__.__name__}). "
                      "You can edit the profile manually later.[/yellow]")
        return {}
    return _parse_yaml_block(out)


def _parse_yaml_block(text: str) -> dict:
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


def _ingest_resume(src: Path) -> str:
    suffix = src.suffix.lower()
    raw: str
    if suffix in {".md", ".markdown", ".txt"}:
        raw = src.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        try:
            import pypdf  # type: ignore
            reader = pypdf.PdfReader(str(src))
            raw = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            console.print("[yellow]PDF parsing needs pypdf:[/yellow] pip install pypdf  — then re-run init.")
            raise typer.Exit(code=1)
    elif suffix in {".docx", ".doc"}:
        try:
            import docx  # type: ignore
            d = docx.Document(str(src))
            raw = "\n".join(p.text for p in d.paragraphs)
        except ImportError:
            console.print("[yellow]DOCX parsing needs python-docx:[/yellow] pip install python-docx  — then re-run init.")
            raise typer.Exit(code=1)
    else:
        raw = src.read_text(encoding="utf-8", errors="replace")

    if suffix in {".md", ".markdown"} and raw.startswith("# "):
        return raw

    console.print("[dim]Extracting structured resume...[/dim]")
    from importlib import resources
    sys_prompt = resources.files("applybrief.prompts").joinpath("resume_extractor.md").read_text()
    try:
        cleaned = llm.complete(system=sys_prompt, user=raw, max_tokens=3000)
    except Exception as e:
        console.print(
            f"[yellow]Couldn't reach the LLM ({e.__class__.__name__}). "
            "Saving raw text as-is. You can edit it later.[/yellow]"
        )
        return raw
    if "EXTRACTION_FAILED" in cleaned:
        console.print("[yellow]Couldn't parse the resume cleanly. Saving raw text.[/yellow]")
        return raw
    return cleaned


# ---------- apply ----------


@app.command()
def apply(
    url: str = typer.Argument(None, help="JD URL (or omit to read from clipboard)."),
    jd_file: Path = typer.Option(
        None, "--jd-file", help="Path to a file with the JD text (instead of a URL)."
    ),
    no_html: bool = typer.Option(
        False, "--no-html", help="Skip rendering the shareable HTML companion."
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Skip auto-opening the HTML in your browser."
    ),
) -> None:
    """Generate an Apply Brief from a JD URL.

    Copy the URL from your browser, then run [bold]applybrief apply[/bold] with no
    argument — it'll read from the clipboard. (Avoids shell escaping for URLs
    with `?` and `&`.)
    """
    p = _ensure_profile()
    resume_md = p.resume_text()
    if not resume_md:
        console.print("[red]No resume on file.[/red] Run [cyan]applybrief init[/cyan] first.")
        raise typer.Exit(code=1)

    jd_text = None
    if jd_file:
        jd_text = jd_file.read_text()
        url = None

    if not url and not jd_text:
        try:
            import pyperclip  # type: ignore
            clip = (pyperclip.paste() or "").strip()
            if _looks_like_url(clip):
                url = clip
                console.print(f"[dim]Using URL from clipboard:[/dim] {clip}")
            elif clip and len(clip) > 200:
                jd_text = clip
                console.print("[dim]Using JD text from clipboard.[/dim]")
        except Exception:  # noqa: BLE001
            pass

    if not url and not jd_text:
        console.print(
            Panel(
                "Nothing to apply to. Three ways:\n\n"
                "  1. Copy a JD URL to your clipboard, then run [cyan]applybrief apply[/cyan]\n"
                "  2. Pass the URL in quotes:   [cyan]applybrief apply '<url>'[/cyan]\n"
                "  3. Paste the JD text into a file:  [cyan]applybrief apply --jd-file ~/jd.txt[/cyan]\n",
                title="No JD provided",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)

    try:
        with console.status("[cyan]Drafting Apply Brief...[/cyan]"):
            md_path, html_path = brief.generate(
                url=url,
                jd_text=jd_text,
                profile=p,
                resume_text=resume_md,
                render_html=not no_html,
            )
    except fetcher.UnsupportedHostError as e:
        console.print(
            Panel(
                f"{e}\n\n"
                "[bold]The fix — paste the JD text instead of the URL:[/bold]\n\n"
                "  1. Open the JD in your browser.\n"
                "  2. Select the JD body — [cyan]Cmd+A[/cyan] then [cyan]Cmd+C[/cyan] \n"
                "     (it's OK to grab the whole page, applybrief sorts it out).\n"
                "  3. Run [cyan]applybrief apply[/cyan] with NO arguments.\n"
                "     It'll see the text on your clipboard and use it.\n\n"
                "[dim]Or save the JD to a file:[/dim] "
                "[cyan]applybrief apply --jd-file ~/Downloads/jd.txt[/cyan]",
                border_style="yellow",
                title="LinkedIn / Indeed / Glassdoor URLs need the JD text",
            )
        )
        raise typer.Exit(code=2)
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "authentication" in msg or "api_key" in msg or "401" in msg:
            console.print(
                Panel(
                    f"Your API key for [bold]{p.llm_model}[/bold] is missing or "
                    "rejected.\n\n"
                    "Set the right env var and re-run:\n"
                    "  • Anthropic models:  [cyan]export ANTHROPIC_API_KEY=sk-ant-...[/cyan]\n"
                    "  • OpenAI models:     [cyan]export OPENAI_API_KEY=sk-...[/cyan]\n"
                    "  • Groq models:       [cyan]export GROQ_API_KEY=gsk-...[/cyan]\n"
                    "  • Ollama:            (no key; just run `ollama serve`)\n\n"
                    "Check current state:  [cyan]applybrief doctor[/cyan]",
                    title="Auth failed",
                    border_style="red",
                )
            )
        else:
            console.print(f"[red]Failed:[/red] {e.__class__.__name__}: {e}")
        raise typer.Exit(code=1)

    panel_body = (
        f"[green bold]✓ Apply Brief drafted.[/green bold]\n\n"
        f"Markdown:  {md_path}\n"
    )
    if html_path:
        panel_body += f"HTML:      {html_path}\n"
    panel_body += (
        "\nOpen it, review, edit, and apply. If you can find a warm contact on "
        "LinkedIn, send a soft DM first."
    )
    console.print(Panel(panel_body, border_style="green"))

    _maybe_open(html_path, no_open)


# ---------- discover ----------


@app.command()
def discover(
    role: str = typer.Option(None, "--role", help="Override target role (default: all from profile)."),
    location: str = typer.Option(None, "--location", help="Override location."),
    hours_old: int = typer.Option(72, "--hours-old", help="Max age of posting in hours (default 72 = 3 days)."),
    sites: str = typer.Option(
        "linkedin,indeed,google,glassdoor,zip_recruiter",
        "--sites",
        help="Comma-separated boards. Choices: linkedin, indeed, google, glassdoor, zip_recruiter, bayt, naukri.",
    ),
    n: int = typer.Option(20, "--n", help="Results per site per role."),
    top: int = typer.Option(50, "--top", help="Top N results to keep after scoring."),
    skip_scoring: bool = typer.Option(
        False, "--no-score", help="Skip LLM scoring (faster, less targeted)."
    ),
    no_html: bool = typer.Option(
        False, "--no-html", help="Skip rendering the shareable HTML companion."
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Skip auto-opening the HTML in your browser."
    ),
) -> None:
    """Search the major job boards and rank by fit against your full profile."""
    p = _ensure_profile()
    site_list = [s.strip() for s in sites.split(",") if s.strip()]

    try:
        with console.status(
            f"[cyan]Searching {', '.join(site_list)} across "
            f"{len(p.target_roles) or 1} role variant(s)...[/cyan]"
        ):
            md_path, rows, html_path = _discover.discover(
                p,
                role=role,
                location=location,
                hours_old=hours_old,
                results_per_site=n,
                sites=site_list,
                skip_scoring=skip_scoring,
                top_n=top,
                render_html=not no_html,
            )
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "authentication" in msg or "api_key" in msg or "401" in msg:
            console.print(
                Panel(
                    f"LLM scoring needs an API key for [bold]{p.llm_model}[/bold].\n"
                    "Either set the env var (e.g. ANTHROPIC_API_KEY) or "
                    "run with [cyan]--no-score[/cyan] to skip ranking.",
                    title="Auth failed",
                    border_style="red",
                )
            )
        else:
            console.print(f"[red]Discovery failed:[/red] {e.__class__.__name__}: {e}")
        raise typer.Exit(code=1)

    if not rows:
        console.print(
            "[yellow]No matches.[/yellow] Try [cyan]--hours-old 168[/cyan] (one week) "
            "or [cyan]--role 'broader term'[/cyan]."
        )
        raise typer.Exit()

    t = Table(title=f"Top {min(15, len(rows))} jobs (of {len(rows)} kept)")
    t.add_column("Fit", justify="right", style="bold")
    t.add_column("Company")
    t.add_column("Title")
    t.add_column("Loc", overflow="fold")
    t.add_column("Posted", style="dim")
    t.add_column("Salary")
    t.add_column("Site", style="dim")
    t.add_column("Why")

    def _fit_color(score) -> str:
        try:
            s = int(score)
        except (TypeError, ValueError):
            return ""
        if s >= 85:
            return f"[bold green]{s}[/bold green]"
        if s >= 70:
            return f"[green]{s}[/green]"
        if s >= 50:
            return f"[yellow]{s}[/yellow]"
        return f"[red]{s}[/red]"

    for r in rows[:15]:
        salary = ""
        if r.get("salary_min") or r.get("salary_max"):
            mn = f"${int(r['salary_min']):,}" if r.get("salary_min") else "?"
            mx = f"${int(r['salary_max']):,}" if r.get("salary_max") else "?"
            salary = f"{mn}–{mx}"
        t.add_row(
            _fit_color(r.get("fit_score", "")),
            r["company"][:25],
            r["title"][:36],
            r["location"][:20],
            r["date_posted"],
            salary,
            r["site"],
            (r.get("fit_why", "") or "")[:60],
        )
    console.print(t)

    panel_body = f"Markdown: {md_path}\n"
    if html_path:
        panel_body += f"HTML:     {html_path}\n"
    panel_body += (
        "\nOpen it, pick a job, copy the URL from your browser, then:\n"
        "  [cyan]applybrief apply[/cyan]              (reads URL from clipboard)\n"
        "  [cyan]applybrief apply '<url>'[/cyan]      (URL in quotes)\n"
    )
    console.print(Panel(panel_body, border_style="cyan"))

    _maybe_open(html_path, no_open)


# ---------- config / doctor ----------


@app.command()
def config() -> None:
    """Show current profile."""
    p = Profile.load()
    if p is None:
        console.print("[yellow]No profile.[/yellow] Run [cyan]applybrief init[/cyan].")
        raise typer.Exit(code=1)
    import yaml
    console.print(Panel(yaml.safe_dump(p.__dict__, sort_keys=False), title=str(profile_path())))


@app.command()
def doctor() -> None:
    """Diagnose environment — keys, deps, paths."""
    checks: list[tuple[str, bool, str]] = []

    p = Profile.load()
    checks.append(("Profile saved", p is not None, str(profile_path())))
    checks.append(("Resume saved", resume_path().exists(), str(resume_path())))

    keys = {
        "ANTHROPIC_API_KEY": "anthropic/",
        "OPENAI_API_KEY": "openai/",
        "GROQ_API_KEY": "groq/",
        "OPENROUTER_API_KEY": "openrouter/",
    }
    model = (p.llm_model if p else "") or os.getenv("APPLYBRIEF_MODEL", "")
    for env_name, prefix in keys.items():
        present = bool(os.getenv(env_name))
        relevant = model.startswith(prefix)
        marker = " (needed for your model)" if relevant else ""
        checks.append((f"{env_name} set", present, marker))

    optional = ["jobspy", "pypdf", "docx", "jinja2", "markdown_it"]
    for mod in optional:
        try:
            __import__(mod)
            checks.append((f"{mod} importable", True, ""))
        except ImportError:
            checks.append((f"{mod} importable", False, "optional"))

    checks.append(("applybrief dir", applybrief_dir().exists(), str(applybrief_dir())))
    checks.append(("`applybrief` on PATH", shutil.which("applybrief") is not None, ""))

    t = Table(title="applybrief doctor")
    t.add_column("Check")
    t.add_column("Status")
    t.add_column("Note", style="dim")
    for label, ok, note in checks:
        t.add_row(label, "[green]✓[/green]" if ok else "[red]✗[/red]", note)
    console.print(t)


if __name__ == "__main__":
    main()
