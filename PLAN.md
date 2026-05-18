# warmapply — Plan

> **Status:** Drafting · **Owner:** Josh · **Repo (target):** github.com/botz-pillar/warmapply · **License:** Apache-2.0 · **Created:** 2026-05-15

---

## What it is

An open-source CLI that turns the job hunt from a soul-crushing volume game into a high-signal pipeline. One command (`warmapply <jd-url>`) produces a single **Apply Brief** with a fit score, a tailored resume diff, a grounded cover letter, a list of 2–3 real warm-intro candidates from your LinkedIn network with personalized draft messages, a hiring-manager dossier, and an interview cheat-sheet.

The differentiator is the **Warm-Intro Engine** — nobody else automates "find a real 2nd-degree contact at this company and draft a personalized referral ask." That's the wow moment.

## Why it exists

Job seekers in 2026 are grinding 100–500 applications to land an interview. The "AI applies to 1000 jobs" category is collapsing: Sonara shut down, LazyApply sits at 2.1 ⭐ on Trustpilot, AIHawk archived itself, LinkedIn now enforces detection at ~15 applies/day. Recruiters flag burst patterns. **Volume is becoming actively counterproductive.**

The market winners (Jobright 4.8 ⭐, Huntr) win on **quality + leverage**. Nobody on the OSS side, and very few on the paid side, has solved the warm-intro layer — the single highest-ROI lever in modern hiring (referrals are 5–10× more likely to land an interview than cold apps).

**warmapply's positioning:** Stop spraying 50 applications. Send 5 great ones, with 5 warm intros first.

## Who it's for

- Mid-career professionals (Josh's friends; healthcare, security, ops) navigating a layoff or career pivot
- People without disposable cash for $30–100/mo career SaaS — they need free or pennies-per-app
- Self-directed enough to run a CLI or paste a URL into a tool, but not engineers
- (Secondary) Developers / Claude Code users via the plugin skin — useful audience for distribution, not the primary user

## Anti-personas — who it's NOT for

- People wanting to blast 500 applications/day (we will refuse to build this)
- Recruiters / ATS-side use (different product)
- Anyone needing fully automated submission with no human in the loop (legal/dignity hazard; we won't do it)

---

## Strategic posture

**Quality + leverage. Locked.** Every product decision flows from this:

- Default behavior caps LinkedIn ops at ≤10/day per user to dodge ban risk
- We do not auto-click submit, ever — the human clicks
- We do not store LinkedIn credentials server-side — we use the user's own browser session via [stickerdaniel/linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server)
- We prefer "1 warm intro + 1 cold app" over "5 cold apps"
- Cover letters are grounded in a specific real signal (company news, blog post, hiring-manager post) — if we can't find one, we say so rather than fabricate

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  warmapply  (Python · Apache-2.0 · pip install)        │
│  ────────────────────────────────────────────────────  │
│   CLI (Typer)                                          │
│   ├─ init · <url> · intros · track · next · mark      │
│                                                        │
│   Agents (markdown prompts)                            │
│   ├─ jd-parser · resume-tailor · cover-letter         │
│   ├─ warm-intro · hiring-manager · interview-prep     │
│   └─ coach                                            │
│                                                        │
│   Provider layer: LiteLLM                              │
│   └─ anthropic | openai | groq | ollama | openrouter  │
│                                                        │
│   Local pipeline DB (SQLite via SQLModel)              │
│   └─ jobs · applications · contacts · activity        │
└─────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
  python-jobspy (MIT)            linkedin-scraper-mcp
  multi-board discovery          (Apache-2.0, subprocess)
                                 user's own browser session
```

**Why each piece:**
- **Python** — every building block in this space is Python; zero translation tax
- **LiteLLM, not LangChain** — AIHawk's death-by-LangChain-version-pin is the cautionary tale; LiteLLM is a single dep, normalizes tool-calling across providers, doesn't rot as fast
- **MCP for LinkedIn** — stickerdaniel solved the hard part (Patchright stealth + 2FA + session persistence); we shell out to it as a subprocess
- **JobSpy as dep** — `pip install python-jobspy` gets us LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter scraping for free; pin a known-good version
- **SQLite local** — no server, no auth, no multi-tenant; a single user's pipeline lives in `~/.warmapply/pipeline.db`
- **Apache-2.0** over MIT for the patent grant

---

## MVP scope

The smallest thing that proves the magic:

```
$ warmapply <jd-url>   →   Apply Brief markdown file
```

No `init`. No DB. No LinkedIn. Just: URL in, killer markdown brief out. **This is the demo gif.** If this single command makes a job-searching friend say "holy shit, I would have paid $50 for this," everything downstream is justified.

### What ships in v1 (≈2 weeks)

| Feature | In v1 | Notes |
|---|---|---|
| `warmapply <url>` → Apply Brief | ✅ | The hero command |
| Fit score (0–100) + honest gap analysis | ✅ | Brutal but not lying |
| Resume diff (specific edits, no fabrication) | ✅ | Markdown diff format |
| Cover letter, grounded in real signal | ✅ | If no signal found, say so |
| `warmapply init` | ✅ | 60-second reverse onboarding |
| Local SQLite pipeline | ✅ | `~/.warmapply/pipeline.db` |
| `warmapply track` | ✅ | Show current pipeline state |
| `warmapply mark applied <slug>` | ✅ | Status tracking |
| Pluggable LLM (Anthropic / OpenAI / Groq / Ollama) | ✅ | LiteLLM |
| Warm-Intro Engine (linkedin-mcp integration) | ✅ | The banger |
| Hiring-manager dossier | ✅ | If JD names them |
| Interview cheat-sheet | ✅ | Top 5 likely Qs + STAR outlines |

### Explicitly NOT in v1

- Workday / Taleo / iCIMS autofill (massive eng cost, post-MVP)
- Web dashboard (CLI + Markdown is enough)
- Inbox parsing for auto-status updates (v2)
- Multi-tenant / auth / billing (maybe never)
- Calendar / interview scheduling (v2)
- Auto-submit to any portal (never; legal + dignity)
- Claude Code plugin skin (week 3 — trivial wrap once core works)

---

## CLI surface

```
warmapply                         # show help + pipeline summary
warmapply init                    # one-time reverse onboarding
warmapply <jd-url>                # generate Apply Brief from a JD URL (the hero)
warmapply intros <slug>           # re-generate warm intros for an existing brief
warmapply track                   # show pipeline kanban (drafted / applied / interviewing / closed)
warmapply mark <status> <slug>    # advance pipeline state
warmapply next                    # coach mode: what should I work on today?
warmapply config                  # view / change LLM provider, model, paths
warmapply doctor                  # diagnose env, deps, MCP servers, API keys
```

## Reverse onboarding (`warmapply init`)

Single command, ≤60 seconds, conversational. Saves to `~/.warmapply/profile.yaml`.

1. **Resume** — drop/paste PDF/DOCX/MD → AI extracts structured profile (work history, skills, education); user confirms key fields
2. **LinkedIn URL** — for the warm-intro graph + profile cross-check
3. **Education** — confirm extracted
4. **Target roles** — free text, AI distills into role tags
5. **Geography** — remote / hybrid / onsite + countries / cities
6. **Comp floor** — minimum acceptable salary
7. **Industries** — focus list + avoid list
8. **LLM provider** — Ollama (free local), Groq (free tier, fast), OpenAI, Anthropic, OpenRouter — BYO key

---

## The Apply Brief (output spec)

Single Markdown file: `~/.warmapply/briefs/YYYY-MM-DD-<company>-<role>.md`

Sections, in order:

1. **Header** — Company · Role · Date · Fit Score · JD URL
2. **Fit Score + Gap Analysis** — 0–100 score + 3-5 bullet honest gaps with "how to honestly bridge each"
3. **Resume Tailoring** — Markdown diff of specific edits (no rewrites, no fabrication)
4. **Cover Letter** — Final draft, grounded in a specific real signal about the company
5. **Warm Intros** — 2–3 real people at this company, each with a personalized draft message
6. **Hiring Manager** — name + LinkedIn (if JD names them) + 3 conversation hooks
7. **Interview Cheat-Sheet** — top 5 likely questions for this role, with STAR outlines using user's actual experience
8. **Next Action** — single line: "Send warm intro to X first" or "Apply directly via Y"

---

## Data model (SQLite)

```
jobs              (id, source, url, company, title, location, posted_at,
                   salary_min, salary_max, jd_raw_md, jd_parsed_json, ingested_at)
applications      (id, job_id, status, brief_path, fit_score, drafted_at,
                   applied_at, response_at, outcome)
contacts          (id, company, name, role, linkedin_url, degree, notes)
intros            (id, application_id, contact_id, message_md, sent_at, response_at)
activity          (id, application_id, kind, payload_json, at)   -- event log
```

Schema lifted/adapted from [dfrysinger/ai-job-hunt-toolkit](https://github.com/dfrysinger/ai-job-hunt-toolkit) (MIT, attributed in NOTICE).

---

## Agents / prompts

Each agent is a Markdown prompt file in `src/warmapply/prompts/`. Loaded at runtime, no Python coupling.

| Agent | Input | Output |
|---|---|---|
| `jd-parser` | JD raw HTML/MD | Structured JD: role, company, must-haves, nice-to-haves, comp, location |
| `resume-tailor` | Profile + parsed JD | Resume diff + fit score + gap analysis |
| `cover-letter` | Profile + parsed JD + company signal | Grounded cover letter draft |
| `company-signal` | Company name | One specific real signal (blog post, news, GH activity) or NONE |
| `warm-intro` | Profile + LinkedIn graph results + JD | 2-3 intros with personalized messages |
| `hiring-manager` | LinkedIn profile of named manager | Dossier + 3 conversation hooks |
| `interview-prep` | Parsed JD + profile | Top 5 likely Qs + STAR outlines |
| `coach` | Pipeline state + recent activity | "What should I work on today?" |

Many prompts will be lifted/adapted from [dfrysinger/ai-job-hunt-toolkit](https://github.com/dfrysinger/ai-job-hunt-toolkit)'s `coach-tools/` and `agents/` directories (MIT, attribution in NOTICE).

---

## Dependencies

| Dep | Purpose | License | Risk |
|---|---|---|---|
| `typer` | CLI framework | MIT | low |
| `rich` | terminal output | MIT | low |
| `litellm` | LLM provider abstraction | MIT | medium — fast-moving |
| `python-jobspy` | multi-board job scraping | MIT | medium — scraper rot |
| `mcp` (Anthropic SDK) | MCP client to talk to linkedin-mcp | MIT | low |
| `sqlmodel` | SQLite ORM | MIT | low |
| `pydantic` | data validation | MIT | low |
| `markdownify` | HTML→MD for JD parsing | MIT | low |
| `pypdf` / `python-docx` | resume parsing | various | low |
| `instructor` (optional) | structured outputs on weaker models | MIT | low |
| **External subprocess:** `linkedin-scraper-mcp` (PyPI) | LinkedIn ops via user's browser | Apache-2.0 | medium — LinkedIn TOS |

**No LangChain. No Selenium. No undetected-chromedriver.**

---

## Risks (pre-mortem)

1. **LinkedIn ban risk for users.** stickerdaniel's "no bans yet" is partial survivorship bias. Mitigation: hard-cap LinkedIn ops at ≤10/day per user, document loudly in README, make LinkedIn ops opt-in per command, never run in the background.

2. **Scraper rot.** JobSpy patches anti-bot 1–3 months after upstream changes. Cliff hits "no jobs found" on day 1. Mitigation: pin known-good JobSpy version, ship Google Jobs as the stable fallback, always allow manual URL paste (the always-works path).

3. **Free-tier LLM quality cliff.** Groq Llama 3.1 8B/70B does decent prose but botches structured outputs (JD parsing, resume diff). Local Ollama on a laptop = 60–120 sec per tailor — kills the snappy demo. Mitigation: tiered model design (cheap model for triage, better model for the Apply Brief itself, cached parsed JD); recommend Anthropic Haiku as the default sweet spot at ~$0.001 per Apply Brief.

4. **AI-detection by recruiters.** Cover letters that read AI-generated get binned. Mitigation: ground every cover letter in a specific real signal; provide a "voice match" pass that compares against user's own writing samples (their resume bullets, LinkedIn About); cap on cover-letter regenerate count to avoid converging on AI-shaped prose.

5. **Brand / scope creep.** "Add Workday autofill, add scheduling, add a web app" — every adjacent ask is bigger than v1. Mitigation: ruthless roadmap discipline; new features ship only after v1 actually helps a real friend land an interview.

---

## Roadmap

### v1.0 — "Apply Brief works" (≈2 weeks)
- `warmapply <url>` produces a complete Apply Brief
- `warmapply init` reverse onboarding
- Local SQLite pipeline + `track` / `mark` / `next`
- Warm-Intro Engine wired to linkedin-mcp
- Apache-2.0 release on github.com/botz-pillar/warmapply
- README + 30-second demo gif
- 3 friends using it

### v1.1 — "Brand voice match"
- "Voice match" pass that grades drafts against user's own writing samples
- Interview cheat-sheet variants per company stage (recruiter screen / hiring manager / panel)
- Tiered model strategy with cost telemetry per Apply Brief

### v1.2 — "Claude Code plugin skin"
- Same engine, exposed as a Claude Code plugin (slash commands + skill)
- Distribution: marketplace listing under botz-pillar

### v2.0 — "Pipeline brain"
- Gmail / Outlook inbox parsing → auto-status updates (interview, rejection, ghost)
- Calendar integration for interview scheduling across time zones
- Resume A/B telemetry (which variant got which response)

### v2.5 — "Honest autofill"
- Workday / Greenhouse / Lever / Ashby form autofill via Chrome extension
- Human always clicks submit
- Open-source extension; pairs with the CLI

### v3+ — (deferred, maybe never)
- Multi-tenant / hosted version
- Mobile app
- "Coach voice" personalization

---

## Open questions

- **Default LLM model.** Anthropic Haiku at ~$0.001/brief is the sweet spot, but requires API key. Should `init` ship a "free tier" recommendation (Groq Llama 70B) and a "best-quality" recommendation (Anthropic Haiku)?
- **Resume input format.** PDF parsing is messy. Should v1 require Markdown or YAML resume to dodge parsing risk, with PDF as best-effort?
- **JD scraping legal posture.** Greenhouse / Lever / Ashby JD URLs are public, scrape-safe. LinkedIn job URLs require auth. Should the hero command refuse LinkedIn job URLs and require Greenhouse/Lever URLs, with a "paste JD text" fallback?
- **Telemetry.** Do we phone home (anonymous usage counts to learn what works)? Default off, opt-in, or never?
- **Naming inside the artifact.** "Apply Brief" or "Briefing" or something more verb-shaped?

---

## Attribution

- Schema and several agent prompts adapted from [dfrysinger/ai-job-hunt-toolkit](https://github.com/dfrysinger/ai-job-hunt-toolkit) (MIT) — see `NOTICE`
- `python-jobspy` from [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy) (MIT)
- `linkedin-scraper-mcp` from [stickerdaniel/linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server) (Apache-2.0)
- LLM abstraction via [LiteLLM](https://github.com/BerriAI/litellm) (MIT)

---

## Decisions log

- **2026-05-15** — Named `warmapply` (Josh). Repo home: `github.com/botz-pillar/warmapply`. License: Apache-2.0. Posture: quality+leverage, OSS, dual-surface (CLI primary, CC plugin secondary). Stack: Python + LiteLLM + JobSpy + linkedin-mcp + SQLite. Anti-pattern: no fork of dfrysinger (TS/Deno + CC-bound), no AIHawk (AGPL + archived), no LangChain.
