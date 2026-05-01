from __future__ import annotations

from pathlib import Path

import httpx
from rich.console import Console

from job_agent.automation import BrowserApplicator
from job_agent.digest import build_digest
from job_agent.filters import is_entry_level_job
from job_agent.llm_client import build_openai_client
from job_agent.matcher import score_job
from job_agent.models import AppConfig, JobPosting, MatchRunResult, TailoredResume
from job_agent.notifications import NotificationDispatcher
from job_agent.providers import CareersPageProvider, GreenhouseProvider, LeverProvider, SerpApiProvider
from job_agent.resume_tailor import tailor_resume
from job_agent.storage import export_application_results, export_jobs, load_sent_job_urls, save_sent_job_urls

console = Console()


def collect_matches(config: AppConfig) -> MatchRunResult:
    providers = _build_providers(config)
    jobs: list[JobPosting] = []
    for provider in providers:
        console.print(f"[cyan]Fetching jobs from {provider.source_name}[/cyan]")
        try:
            jobs.extend(provider.fetch_jobs(config.search))
        except httpx.HTTPError as exc:
            console.print(f"[yellow]Skipping {provider.source_name}: {exc}[/yellow]")
        except Exception as exc:
            console.print(f"[yellow]Skipping {provider.source_name} due to unexpected error: {exc}[/yellow]")

    ranked = sorted(
        (score_job(job, config.profile, config.search) for job in jobs),
        key=lambda job: job.score,
        reverse=True,
    )
    ranked = [job for job in _dedupe_jobs(ranked) if is_entry_level_job(job, config.search)]

    export_jobs(ranked, Path("data/jobs/ranked_jobs.json"))
    console.print(f"[green]Exported {len(ranked)} ranked jobs.[/green]")

    sent_store = Path("data/jobs/sent_jobs.json")
    sent_urls = load_sent_job_urls(sent_store)
    fresh_jobs = [job for job in ranked if job.url not in sent_urls]
    console.print(f"[green]Found {len(fresh_jobs)} new jobs not previously sent.[/green]")
    return MatchRunResult(ranked_jobs=ranked, fresh_jobs=fresh_jobs)


def run_pipeline(env_api_key: str | None, config: AppConfig) -> MatchRunResult:
    result = collect_matches(config)
    fresh_jobs = result.fresh_jobs

    resumes: dict[str, TailoredResume] = {}
    if env_api_key:
        client = build_openai_client(env_api_key)
        base_resume = config.profile.base_resume_path.read_text(encoding="utf-8")
        prompt_path = Path("src/job_agent/prompts/resume_tailor.txt")
        for job in fresh_jobs[: min(10, len(fresh_jobs))]:
            tailored = tailor_resume(
                client=client,
                model=config.llm.model,
                prompt_path=prompt_path,
                base_resume_markdown=base_resume,
                profile=config.profile,
                job=job,
                output_dir=Path("data/exports"),
            )
            resumes[tailored.job_url] = tailored
            console.print(f"[green]Tailored resume for {job.company} - {job.title}[/green]")
    else:
        console.print("[yellow]OPENAI_API_KEY not set. Skipping resume tailoring.[/yellow]")

    _send_notifications_if_needed(config, result)

    applicator = BrowserApplicator(config.automation)
    results = applicator.run(fresh_jobs[: min(5, len(fresh_jobs))], config.profile, resumes)
    export_application_results(results, Path("data/exports/application_results.json"))
    console.print("[green]Application review queue exported.[/green]")
    return result


def notify_matches(config: AppConfig, result: MatchRunResult) -> MatchRunResult:
    _send_notifications_if_needed(config, result)
    return result


def _build_providers(config: AppConfig):
    providers = []
    greenhouse = config.sources.get("greenhouse")
    if greenhouse and greenhouse.enabled:
        providers.append(GreenhouseProvider(greenhouse.boards))

    lever = config.sources.get("lever")
    if lever and lever.enabled:
        providers.append(LeverProvider(lever.boards))

    careers = config.sources.get("careers")
    if careers and careers.enabled:
