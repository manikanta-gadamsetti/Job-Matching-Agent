from __future__ import annotations

import json
from pathlib import Path

from job_agent.models import ApplicationOutcome, JobPosting


def export_jobs(jobs: list[JobPosting], path: Path) -> None:
    path.write_text(
        json.dumps([job.model_dump(mode="json") for job in jobs], indent=2),
        encoding="utf-8",
    )


def export_application_results(results: list[ApplicationOutcome], path: Path) -> None:
    path.write_text(
        json.dumps([result.model_dump(mode="json") for result in results], indent=2),
        encoding="utf-8",
    )


def load_sent_job_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return set(raw)


def save_sent_job_urls(urls: set[str], path: Path) -> None:
    path.write_text(json.dumps(sorted(urls), indent=2), encoding="utf-8")
