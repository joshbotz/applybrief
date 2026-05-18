# ApplyBrief

*The brief you wish someone wrote for every job you applied to.*

A couple of years ago I sent 350+ job applications over six months. A handful of interviews. Two offers. Two years later I still get rejection notices in my inbox. I built this for friends going through the same thing now, and I'm open-sourcing it so other people can use it too. It's a small command-line tool that finds jobs worth your time and writes the boring parts of the application for you. Honest, not hyped. Runs on your Mac or Windows PC. Free.

## What you get

- **A short-list of jobs scored against your background.** Not 500 listings — 10 to 30 that actually match what you said you want.
- **A one-page brief for any job you like.** Where you fit, where you don't, a cover letter draft, interview prep, and a manual outreach plan for finding a warm intro on LinkedIn.
- **Honest about bad fits.** If you're not a match, the brief tells you to skip — it won't pretend to write a cover letter for a job you shouldn't be applying to.

## Install

**Mac.** Paste into Terminal:

```
curl -fsSL https://raw.githubusercontent.com/botz-pillar/applybrief/main/install.sh | bash
```

**Windows (10/11).** Paste into PowerShell:

```
iex (iwr -useb https://raw.githubusercontent.com/botz-pillar/applybrief/main/install.ps1).Content
```

**Linux.** Needs Python 3.11+ and pipx already installed:

```
pipx install git+https://github.com/botz-pillar/applybrief.git@v0.1.0
```

<details>
<summary>What the installer actually does</summary>

It checks for a package manager (Homebrew on Mac, winget on Windows), Python 3.11+, and pipx — installs anything missing — then installs ApplyBrief itself from a pinned GitHub release tag. Mac details: [INSTALL_NOTES.md](INSTALL_NOTES.md). Windows details: [INSTALL_NOTES_WINDOWS.md](INSTALL_NOTES_WINDOWS.md). No telemetry, no shell-config changes beyond `pipx ensurepath`.

</details>

## Use it (3 commands)

**`applybrief init`** — one-time setup. Point it at your resume. Answer four short questions in your own words. Takes about a minute. Your profile lives on your machine.

**`applybrief discover`** — finds jobs. It searches LinkedIn, Indeed, Google Jobs, Glassdoor, and ZipRecruiter, then scores each posting 0–100 against your profile. You get a sortable HTML page that opens in your browser plus a markdown file.

**`applybrief apply <a job url>`** — go deep on one role. Give it a JD URL (or copy the URL and just run `applybrief apply` — it reads your clipboard). You get a one-page brief in your browser: fit assessment, resume tailoring notes, a draft cover letter (with a Copy button), interview prep, and a manual outreach plan.

You read each brief, edit the cover letter, and apply. If you can find a warm contact on LinkedIn, the brief tells you exactly who to look for — send a soft DM before you submit.

## What it costs

Pennies a day with the recommended AI model. $0 if you run it locally with Ollama. You bring your own API key — there is no ApplyBrief subscription and no server.

<details>
<summary>Cost detail</summary>

| Model | Per Apply Brief | Per `discover` run (~30 jobs) |
|---|---|---|
| Anthropic Claude Haiku (default) | ~$0.001 | ~$0.02 |
| Anthropic Claude Sonnet | ~$0.02 | ~$0.50 |
| Groq Llama 3.1 70B | ~$0.0005 | ~$0.01 |
| Ollama (local) | $0 | $0 |

You pay the model provider directly. ApplyBrief takes no cut.

</details>

## What it does with your data

- Your resume and profile stay on your machine (`~/Library/Application Support/applybrief/` on Mac, `%LOCALAPPDATA%\applybrief\` on Windows).
- They go to the AI provider you picked (Anthropic, OpenAI, Groq, or local Ollama) only when a brief needs to be written.
- No tracking. No analytics. No server. The code is open source — read every line.

## A few honest notes

- This won't get you a job. You will. ApplyBrief saves you the hours you'd waste on the wrong applications.
- Edit the cover letter. Recruiters can smell unedited AI output.
- 5 great applications beats 50 mediocre ones. The whole point of the tool is to make "great" cheaper, not "mediocre" faster.
- If you can find a warm intro on LinkedIn, send it before you submit. Referrals are 4–10x more likely to lead to a hire than cold applications.

## What's not great yet (v0.1.0 is early — your feedback shapes v0.2)

I'm shipping this honest. Things that work well today:
- `apply` produces high-quality briefs that refuse to fabricate (validated against 12 real cleared/federal JDs at avg 4.9/5 quality).
- `discover` works great for defense / federal / cleared-roles space (Indeed indexes those densely).
- HTML output is clean and shareable on both Mac and Windows.

Things that don't work well yet — please tell me when you hit one:

- **`apply` on LinkedIn / Indeed / Glassdoor URLs is unsupported** (their pages are JavaScript-rendered and the fetcher can't read them). The workaround the tool tells you about: open the JD page, hit Cmd+A then Cmd+C, then run `applybrief apply` with no arguments — it picks up the JD text from your clipboard. Greenhouse, Lever, Ashby, and company career-page URLs work directly.
- **`discover` results vary by domain.** Defense/cleared/federal: lots of dense, high-fit results. Cloud security, GRC, marketing, ops, sales: thinner pickings — many roles live on LinkedIn or niche boards that JobSpy can't easily scrape. Widening source coverage is on the roadmap.
- **Glassdoor and ZipRecruiter are often blocked** without a proxy. They're in the default site list but frequently 400/403. LinkedIn, Indeed, and Google Jobs work reliably.
- **The fit scorer is sometimes generous** with stretch roles. Read each brief — it's honest about gaps but the headline score can land 5–10 points high. Trust the gaps section, not just the number.
- **Windows install has been Mac-side dry-run validated but not yet tested on a real Windows box.** If you're a Windows user trying this first — bless you, and please tell me anything that breaks.
- **No warm-intro engine yet.** The brief tells you exactly who to look for on LinkedIn and includes a sample DM, but the lookup is manual. Building the engine is the next chunk of work.

**Tell me what's broken or weak.** Open an issue: [github.com/botz-pillar/applybrief/issues](https://github.com/botz-pillar/applybrief/issues). Email me: josh@pillarsecurity.io. I'm building this with friends in mind — every report makes the next version better.

## FAQ

**Do I need a GitHub account?** No. The install command above downloads what you need directly.

**I've never used Terminal / PowerShell.** Mac: Cmd+Space, type "Terminal", hit Enter. Windows: Start menu, type "PowerShell", click it. Paste the install command. Hit Enter. Type your password when it asks. That's the hardest part.

**Is it really free?** Yes. You pay the AI provider you choose (usually pennies a day) or run it for $0 with local Ollama.

**Will this work on Windows?** Yes — v0.1.0 ships with a native Windows installer.

**What if I get stuck?** Email me: josh@pillarsecurity.io. I read every one.

## Roadmap

Warm-intro engine (LinkedIn 2nd-degree lookup) is the next big thing. Other stuff in [CHANGELOG.md](CHANGELOG.md).

## License & author

Apache 2.0. Built by Josh Botz — [@joshthebotz](https://joshthebotz.com). If ApplyBrief helped you land something, I'd love to hear about it: josh@pillarsecurity.io.
