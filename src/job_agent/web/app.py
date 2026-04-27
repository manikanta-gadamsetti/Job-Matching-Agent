from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from job_agent.config import load_config
from job_agent.pipeline import collect_matches, notify_matches
from job_agent.storage import load_sent_job_urls

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[2]
CONFIG_PATH = PROJECT_DIR / "config.yaml"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Job Matching Agent")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    _, config = load_config()
    sent_count = len(load_sent_job_urls(PROJECT_DIR / "data/jobs/sent_jobs.json"))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": config.profile,
            "search": config.search,
            "sources": config.sources,
            "sent_count": sent_count,
            "message": None,
            "jobs": [],
        },
    )


@app.post("/profile", response_class=HTMLResponse)
def save_profile(
    request: Request,
    candidate_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    total_experience_years: int = Form(...),
    target_roles: str = Form(...),
    preferred_locations: str = Form(...),
    certifications: str = Form(""),
    experience_highlights: str = Form(""),
) -> HTMLResponse:
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw["profile"]["candidate_name"] = candidate_name
    raw["profile"]["email"] = email
    raw["profile"]["phone"] = phone
    raw["profile"]["total_experience_years"] = total_experience_years
    raw["profile"]["target_roles"] = _split_lines(target_roles)
    raw["profile"]["preferred_locations"] = _split_lines(preferred_locations)
    raw["profile"]["certifications"] = _split_lines(certifications)
    raw["profile"]["experience_highlights"] = _split_lines(experience_highlights)
    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return RedirectResponse(url="/?saved=1", status_code=303)


@app.post("/run", response_class=HTMLResponse)
def run_agent(request: Request) -> HTMLResponse:
    _, config = load_config()
    result = collect_matches(config)
    notify_matches(config, result)
    sent_count = len(load_sent_job_urls(PROJECT_DIR / "data/jobs/sent_jobs.json"))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": config.profile,
            "search": config.search,
            "sources": config.sources,
            "sent_count": sent_count,
            "message": f"Found {len(result.fresh_jobs)} fresh jobs and sent {result.sent_count} notifications.",
            "jobs": result.fresh_jobs[:20],
        },
    )


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
