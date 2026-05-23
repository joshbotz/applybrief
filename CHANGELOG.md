# Changelog

## 0.1.0 — 2026-05-17

**Breaking — project renamed from `warmapply` to `ApplyBrief`.**

The original name implied a warm-intro engine that isn't built yet. ApplyBrief names what the tool actually does today: it produces an honest one-page brief for every job you might apply to.

### Breaking
- CLI verb changed: `warmapply <args>` → `applybrief <args>`.
- Python package: `warmapply` → `applybrief`.
- Data directory: `~/Library/Application Support/warmapply/` → `~/Library/Application Support/applybrief/`. Existing data is NOT migrated — run `applybrief init` again with your résumé.
- Env var: `WARMAPPLY_MODEL` → `APPLYBRIEF_MODEL`.
- Install URL: `github.com/botz-pillar/warmapply` → `github.com/joshbotz/applybrief`.

### How to upgrade

```
pipx uninstall warmapply
curl -fsSL https://raw.githubusercontent.com/joshbotz/applybrief/main/install.sh | bash
applybrief init
```

### Added (since 0.0.4)
- Public open-source release — first version made for sharing beyond a handful of friends.
- README rewritten for non-technical job-seekers.
- README "What's not great yet" section with honest disclosure of v0.1.0 limitations and feedback CTA.
- `applybrief init --resume <path>` flag — pass your résumé directly without the interactive prompt.
- `pypdf` and `python-docx` promoted from optional to required dependencies so PDF/DOCX résumés just work.
- Friendlier error when `apply` gets a LinkedIn / Indeed / Glassdoor URL — tells the user exactly how to use the clipboard-paste workflow instead.

### Note on the warm-intro engine
Still on the roadmap. Will not block public release. When it ships, the briefs will auto-surface 1st/2nd-degree LinkedIn contacts at the target company; for now you find the warm intro yourself and the brief tells you exactly who to look for.

---

## 0.0.4 — 2026-05-17

Big release. HTML output for sharing + native Windows installer + brand-aligned visuals + opt-out flags wired through.

### Added
- **HTML output** for every Apply Brief and Discoveries report. Self-contained single-file HTML (Tailwind via CDN, no build step). Opens automatically in your browser on generation. Prints cleanly to PDF.
- **`--no-html`** flag on `apply` and `discover` — skip the HTML render if you only want the markdown.
- **`--no-open`** flag on `apply` and `discover` — generate HTML but don't auto-launch the browser.
- **Brand visuals** — dark mode (purple `#8B5CF6` primary, cyan `#00E5CC` for Next Action callouts, white text on `#2B2B2B`). Matches Josh's existing brand palette.
- **Native Windows installer (`install.ps1`)** — PowerShell + winget, `#Requires -Version 5.1`, `-DryRun` parameter, plain-English error handling matching the Mac installer's voice. Installs Python 3.12 + pipx + warmapply.
- **`INSTALL_NOTES_WINDOWS.md`** — companion explainer for what the Windows installer does, expected UAC/SmartScreen/exec-policy behavior, WSL2 fallback for older Windows.

### Changed
- `brief.generate()` now returns `(md_path, html_path | None)` — HTML is best-effort; markdown stays canonical.
- `_discover.discover()` now returns `(md_path, rows, html_path | None)` — same pattern.
- `doctor` checks for `jinja2` and `markdown_it` as optional deps (used for HTML rendering).
- README updated with the native Windows install path. WSL2 still documented as a fallback for older Windows boxes.

### Dependencies
- Added: `jinja2>=3.1`, `markdown-it-py>=3.0`

### Known issues
- Ashby fetcher occasionally fails on closed/filled postings — the tool refuses to fabricate (correct behavior) but the error message could be friendlier.
- Windows installer has not yet been tested on a real Windows box — Mac-side parse and dry-run checks only. Awaiting friend validation + Josh's Dell.

---

## 0.0.3 — 2026-05-17

First Mac-shippable release after a full battle-test of the apply pipeline on 12 real defense/cleared JDs (avg quality 4.9/5).

### Fixed
- **Apply Brief:** dropped non-existent `warmapply intros` subcommand reference; the Warm Outreach section now gives concrete manual LinkedIn guidance.
- **Apply Brief:** travel-conflict callout now leads the Next Action when the profile says "limited travel" and the JD says ≥20% — never buried.
- **Apply Brief:** mandatory salary-verification step when the JD has no posted range and the profile has a comp floor set.
- **Apply Brief:** explicit clearance crosswalk reference baked into the prompt (DoE Q vs TS vs TS/SCI vs polygraph).
- **Apply Brief:** bad-fit refusal made explicit — when fit < 40 or gaps are unbluffable, skip the cover letter and interview prep with a stated reason.
- **README / social copy / install script / pyproject description:** removed the "with 5 warm intros first" promise. New tagline: *"Stop spraying 50 applications. Send 5 deeply-researched ones."*
- **CLI status banner** updated so it no longer implies the tool produced warm intros it didn't.

### Roadmap (still future)
- Warm-intro engine (LinkedIn 2nd-degree lookup) — the headline differentiator and the hardest part. No date.
- SQLite pipeline tracker (`warmapply track / mark / next`).
- Claude Code plugin skin.
- PyPI release + warmapply.dev landing page.
