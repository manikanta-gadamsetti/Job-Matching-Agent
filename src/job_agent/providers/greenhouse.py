from __future__ import annotations

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from job_agent.models import JobPosting, SearchConfig
from job_agent.providers.base import JobSourceProvider


class GreenhouseProvider(JobSourceProvider):
    source_name = "greenhouse"

    def __init__(self, boards: list[str]) -> None:
        self.boards = boards

    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        for board in self.boards:
            response = httpx.get(board, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            company = urlparse(board).path.split("=")[-1] or "unknown"
            for link in soup.select("a[href]"):
                title = link.get_text(" ", strip=True)
                href = link.get("href", "")
                if not title or "/jobs/" not in href:
                    continue
                job_url = href if href.startswith("http") else f"https://boards.greenhouse.io{href}"
                parent_text = link.parent.get_text(" ", strip=True)
                location = parent_text.replace(title, "").strip(" -") or "Unknown"
                if not _matches_search(title, location, search):
                    continue
                jobs.append(
                    JobPosting(
                        source=self.source_name,
                        title=title,
                        company=company.title(),
                        location=location,
                        url=job_url,
                        description=_fetch_description(job_url),
                        remote="remote" in location.lower(),
                    )
                )
                if len(jobs) >= search.max_jobs_per_source:
                    break
        return jobs


def _fetch_description(job_url: str) -> str:
    response = httpx.get(job_url, timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    body = soup.get_text("\n", strip=True)
    return body[:15000]


def _matches_search(title: str, location: str, search: SearchConfig) -> bool:
    title_l = title.lower()
    location_l = location.lower()
    title_match = any(keyword.lower() in title_l for keyword in search.keywords)
    location_match = any(loc.lower() in location_l for loc in search.locations) or "remote" in location_l
    return title_match and location_match
