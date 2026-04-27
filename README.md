# Job Matching Agent

This is a Python starter for:

- discovering jobs from search results, ATS boards, and public career pages
- filtering them for your profile and 0-1 years experience
- ranking and deduplicating them
- sending matching jobs to you by email or WhatsApp

## What it does

- Searches multiple sources using provider modules.
- Scores jobs against your target roles, locations, certifications, and junior-level fit.
- Filters for fresher or 0-1 year openings.
- Saves new matches and avoids re-sending duplicates.
- Sends a digest with job title, company, location, score, and link.

## Source strategy

Direct scraping of LinkedIn, Naukri, and Indeed can be fragile or restricted. This project is designed to:

- Prefer ATS boards like Greenhouse and Lever.
- Support public company career pages.
- Optionally use a search API to discover public listings across LinkedIn, Naukri, Indeed, and careers pages.
- Keep the source layer pluggable so you can add site-specific collectors later.

## Quick start

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
playwright install chromium
```

2. Copy `.env.example` to `.env`. `OPENAI_API_KEY` is optional unless you want tailored resumes.
3. Edit `config.yaml` with your details, preferred locations, and notification settings.
4. Add your base resume to `data/resumes/base_resume.md`.
5. Run the pipeline:

```powershell
job-agent run
```

The run command will discover jobs, rank them, save them to `data/jobs/ranked_jobs.json`, persist already-sent links, and send only fresh matches.

## Web app

You can run the dashboard locally with:

```powershell
uvicorn main:app --reload
```

The website lets you:

- update your profile
- trigger a matching run
- view the latest fresh matches

## Streamlit Cloud

This repo is now also prepared for Streamlit Community Cloud with:

- [streamlit_app.py](C:/Users/Manik/Documents/Codex/2026-04-28/hello/streamlit_app.py)
- [requirements.txt](C:/Users/Manik/Documents/Codex/2026-04-28/hello/requirements.txt)

To run it locally:

```powershell
streamlit run streamlit_app.py
```

To deploy on Streamlit Community Cloud:

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Click `Create app`.
4. Select your GitHub repo and set the entrypoint file to `streamlit_app.py`.
5. In Advanced settings, choose Python `3.11` or `3.12` and add secrets from your `.env`.
6. Deploy.

## Deploy

This repo is ready for a straightforward GitHub + Render flow:

1. Push the project to GitHub.
2. Create a new Render web service from the repo.
3. Add environment variables from `.env.example`.
4. Deploy using the included `Dockerfile` and `render.yaml`.

You can also deploy the same app to Railway, Fly.io, or any Docker-compatible host.

## Notifications

- Email uses SMTP with an app password.
- WhatsApp uses Twilio WhatsApp messaging.
- You can enable either or both in `config.yaml`.
