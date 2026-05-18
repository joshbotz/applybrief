# ApplyBrief — Launch Posts

Repo: https://github.com/botz-pillar/applybrief
Tagline: *The brief you wish someone wrote for every job you applied to.*

---

## LinkedIn

A couple of years ago I sent 350+ job applications over six months. Got a handful of interviews. Eventually got 2 offers. I still get rejection notices in my inbox two years later.

I'm employed now. But I have friends who aren't, and I keep watching them run the same playbook I ran. It didn't work for me. It's working less for them.

The math is the problem.

The "spray 500 résumés" approach used to work because the funnel was wide. It isn't anymore. ATS filters got smarter. AI-generated cover letters are now a negative signal, not a neutral one. The volume tools that promised to "apply to 1,000 jobs while you sleep" are the exact pattern recruiters now filter against.

Meanwhile the referral data hasn't moved: referrals are 4–10x more likely to lead to a hire than cold applications (Jobvite Recruiter Nation Reports; Greenhouse hiring data). One warm intro beats fifty cold sends.

So I built the tool I wish I'd had. It's for the people in my life grinding apps right now, and anyone else in the same spot.

It's called ApplyBrief. Open source. Runs on your Mac or Windows PC. Three commands:

`applybrief init` — reads your résumé, builds your profile
`applybrief discover` — pulls jobs from 5 boards, ranks them against your background
`applybrief apply <url>` — generates a tailored cover letter draft and a one-page interview prep brief for any JD (you edit before sending — that part still matters)

You bring your own LLM key (Anthropic, OpenAI, Groq, or free local Ollama). Your résumé only goes to the model provider you picked — or nowhere at all if you use local Ollama. Costs pennies per application. Apache-2.0 licensed. Works for any role, not just engineering. No subscription, no upsell, no "premium tier."

The point isn't to apply faster. It's to apply *better*, to *fewer* roles, with a real reason you want each one.

If you or someone you know is in the apply-grind right now, it's free. Use it, fork it, tell me what's broken.

github.com/botz-pillar/applybrief

#opensource #jobsearch

---

## Skool — AI Cloud Security Lab

Hey team — quick one, slightly off-topic for the lab but I want you to have it.

A couple of years ago I sent 350+ job applications over six months. Got a handful of interviews, eventually got 2 offers. Still get rejection notices for those apps two years later. I have multiple friends in that same grind right now and the math has only gotten worse — ATS filters and AI-cover-letter detectors have caught up to the volume-blast playbook. Referrals are 4–10x more likely to lead to a hire than cold applications (Jobvite + Greenhouse data).

So I built the tool I wish I'd had. It's a small CLI called ApplyBrief. Open source, runs locally, three commands: profile yourself from your résumé, discover ranked jobs, generate a tailored cover letter draft + interview prep brief for any role.

It's outside what we do in the lab, but I'm sharing it here because (1) some of you are job hunting or know someone who is, and (2) it's a clean example of "small Python CLI, BYO LLM key, costs pennies" — same shape as a lot of the tooling we build in here.

Repo: github.com/botz-pillar/applybrief

Free. Apache-2.0. Fork it, break it, send it to a friend who needs it.

— Josh

---

## Facebook

I sent 350+ job applications over six months a couple of years back. Got a handful of interviews, eventually got 2 offers, and I still get rejection emails for those applications two years later. I have friends out of work right now running the same playbook and it's working even less than it did for me.

The "blast 500 résumés" trick doesn't work anymore because the filters caught up. The thing that still works is the oldest thing: a warm intro. Referrals are 4–10 times more likely to lead to a hire than cold applications (Jobvite + Greenhouse data). The whole game shifted from volume back to relationships and most people haven't noticed.

So this week I built the tool I wish I'd had. Free. It reads your résumé, finds you 10 good-fit jobs instead of 500 mediocre ones, and writes a tailored cover letter draft + a one-page interview prep brief for each one you actually want to apply to. Runs on your Mac or Windows PC, costs pennies, open source.

If you're job hunting right now, or know someone who is — here's the repo: https://github.com/botz-pillar/applybrief

Please pass it along to anyone who needs it.

---

## Instagram

### Caption

I sent 350+ job applications over six months a couple of years ago. A handful of interviews. Eventually 2 offers. And I still get rejection notices in my inbox today.

I didn't have a tool like this. I wish I had.

The spray-and-pray era is over — ATS filters and AI-cover-letter detectors caught up. What still works is what always worked: a warm intro and a tailored application.

So I built this for the people in my life still grinding apps. Free. Open source.

Link in bio. Apache-2.0. Share it with a friend who needs it.

#jobsearch #laidoff #opensource #careeradvice #buildinpublic

### Carousel script (6 slides)

**Slide 1 — Hook**
I sent 350+ job apps over 6 months.
2 offers. Still getting rejection emails 2 years later.
I built the tool I wish I'd had.

**Slide 2 — The problem**
The "blast 500 résumés" playbook is dead.
ATS filters got smarter.
AI-generated cover letters are now a negative signal.
Volume = noise.

**Slide 3 — The insight**
Referrals are 4–10x more likely to lead to a hire than cold applications.
(Jobvite Recruiter Nation Reports + Greenhouse hiring data.)
One warm intro beats fifty cold sends.

**Slide 4 — What ApplyBrief does**
A free CLI. Three commands.
`init` — profile from your résumé
`discover` — 10 ranked jobs, not 500
`apply` — tailored cover letter draft + interview prep for any role

**Slide 5 — Who it's for**
If you or someone you love is job-hunting right now —
this is for you.
Free. Open source. Runs on your laptop.

**Slide 6 — CTA**
github.com/botz-pillar/applybrief
Link in bio.
Share with a friend who's grinding apps.

---

## Show HN

**Title:**
Show HN: ApplyBrief – a CLI for sending 5 great job applications instead of 50 bad ones

**Body:**

A couple of years ago I sent 350+ applications over six months, got a handful of interviews, and eventually 2 offers. I still get rejection emails for those applications today. I have friends running the same playbook right now and it's working even less than it did for me, so I built the tool I wish I'd had.

The "apply to 500 jobs" playbook is dead, and most candidates haven't caught up. Three things changed at once: ATS filters got better at de-duping templated applications, recruiters now actively filter for the fingerprints of volume-apply tools (Sonara, LazyApply, AIHawk), and AI-generated cover letters went from a neutral signal to a negative one inside maybe 18 months. Meanwhile referrals are still 4–10x more likely to lead to a hire than cold applications (Jobvite Recruiter Nation Reports; Greenhouse hiring data).

vs. Sonara / LazyApply / AIHawk: those are volume tools that auto-blast. ApplyBrief is the opposite — it helps you send fewer, better applications, ideally with a warm intro you find yourself.

Three commands — `init` (profile from résumé), `discover` (LLM-ranked jobs from 5 boards via JobSpy), `apply <url>` (tailored cover letter draft + a one-page interview prep brief from any JD). You always edit the draft before sending.

Stack notes for the HN crowd: LiteLLM so the user picks the provider (Anthropic, OpenAI, Groq, or free local Ollama). JobSpy for board scraping. Plain Python, runs on your Mac or Windows PC, no server, no account, no telemetry. Cost on Claude Haiku is roughly $0.001 per Apply Brief and $0.02 per discover run (~30 jobs); local Ollama is $0. Your résumé goes only to the model provider you chose — or nowhere at all if you use Ollama.

What's NOT built yet: the piece I actually want most, a warm-intro engine that uses your own LinkedIn session to surface 2nd-degree contacts at target companies. That's the hardest part and the next chunk of work. I shipped the rest first because my friends need it now and I'd rather have something useful in their hands than nothing while I figure out the harder problem.

Apache-2.0. Feedback welcome, especially from anyone who's hired in the last 12 months.

https://github.com/botz-pillar/applybrief

---

## Personal email to friends

**Subject:** Built you something

**Body:**

Hey —

Heard you've been grinding apps. The math on cold sends is genuinely broken right now — ATS filters and AI-cover-letter detectors have caught up, and referrals are 4–10x more likely to land a hire than cold applications. I lived this myself a couple of years ago (350+ apps over six months, 2 offers, still get rejection emails about it), and I wish I'd had a tool like this back then. So I built one — for you, and for a few other people in my life in the same spot.

It's called ApplyBrief. Free command-line tool. It reads your résumé, finds you ~10 well-matched jobs instead of 500 random ones, and writes a tailored cover letter draft + a short interview prep brief for any role you actually want to apply to. You always edit the draft before sending.

Runs on your Mac or Windows PC. Costs pennies per application (you bring your own AI key — I'll help you set that up if you want).

Repo: https://github.com/botz-pillar/applybrief

Try it. Tell me what's broken. And let me know how I can help beyond this — happy to do mock interviews, intro you to people, review your résumé, whatever.

— Josh

P.S. One-line install on the repo README. Takes about 5 minutes start to finish.
