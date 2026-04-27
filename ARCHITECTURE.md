# High-Level Architecture

## 1. Ingestion Layer

- `GreenhouseProvider` and `LeverProvider` collect jobs from structured career boards.
- Future providers can be added for company career pages, CSV imports, referrals, or user-curated links.
- For sites like LinkedIn and Naukri, prefer browser-assisted collection with a signed-in human session rather than unattended scraping.

## 2. Matching Layer

- `matcher.py` scores each job against:
  - target role titles
  - preferred locations
  - certification signals
  - keyword overlap
- Ranked jobs are exported to `data/jobs/ranked_jobs.json`.

## 3. Resume Tailoring Layer

- `resume_tailor.py` sends:
  - candidate profile
  - base resume
  - raw job description
  - tailoring rules
- Output is a per-job Markdown resume in `data/exports/`.
- Guardrail: tailor only what is already true.

## 4. Application Layer

- `automation/browser.py` launches a Playwright browser with persisted session state.
- The agent can:
  - open the job page
  - detect likely login or CAPTCHA screens
  - fill common low-risk fields
  - pause for human review before submit
- This is intentionally semi-autonomous.

## 5. Orchestration Layer

- `pipeline.py` coordinates sourcing, scoring, tailoring, and application assistance.
- `cli.py` exposes the pipeline as `job-agent run`.

## 6. Recommended Future Upgrades

- Add a queue and scheduler for recurring searches.
- Persist jobs and application state in SQLite or Postgres.
- Render tailored Markdown or LaTeX resumes to PDF.
- Add company-specific form mappers.
- Add recruiter-email drafting and referral tracking.

# Phased Build Roadmap

## Phase 1: Stable Foundations

Goal: Get reliable sourcing, ranking, and resume tailoring working.

- Finalize your base resume in Markdown or LaTeX.
- Expand provider coverage for company pages you actually target.
- Add deduplication by normalized URL and title-company hash.
- Improve matching with a weighted skill taxonomy instead of plain keyword scoring.

## Phase 2: Application Assistance

Goal: Reduce repetitive application work without risky full autonomy.

- Add resume upload support for supported forms.
- Add answer templates for common questions like notice period, work authorization, and salary expectations.
- Add a review dashboard that shows job, score, tailored resume path, and status.

## Phase 3: Human-in-the-Loop Agent

Goal: Make it feel agentic while keeping approval checkpoints.

- Add a planner that decides:
  - which jobs are worth applying to
  - whether a resume should be tailored
  - whether the application flow is safe to automate
- Add confirmation gates before:
  - submitting an application
  - reusing an old answer
  - applying to a low-confidence match

## Phase 4: Operational Hardening

Goal: Make the system dependable.

- Add structured logs and screenshots on automation failure.
- Add retries with backoff for fetch failures.
- Add metrics on sourcing yield, match quality, and application completion rate.

# Anti-Bot and Account Safety

## What to do

- Use your own browser session and persist Playwright storage state after manual login.
- Keep request volume low and human-paced.
- Use automation mainly on company-hosted ATS flows like Greenhouse and Lever.
- Stop when a site shows CAPTCHA, MFA, or unusual verification and complete that step manually.

## What not to do

- Do not script around CAPTCHA or verification challenges.
- Do not run high-volume unattended applications.
- Do not rotate identities, fingerprints, or proxies to imitate evasion.
- Do not auto-submit to platforms that prohibit this behavior in their terms.

# Suggested Tech Stack

- Orchestration: plain Python service first, then LangGraph if you need multi-step agent state.
- LLM: OpenAI Responses API for resume tailoring and application-answer drafting.
- Browser automation: Playwright.
- Parsing: BeautifulSoup plus targeted parsers for ATS pages.
- Persistence: start with JSON, then move to SQLite/Postgres.
- Scheduling: APScheduler or a lightweight worker queue.
