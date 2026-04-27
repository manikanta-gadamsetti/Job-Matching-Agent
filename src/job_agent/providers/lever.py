from __future__ import annotations

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from job_agent.models import JobPosting, SearchConfig
from job_agent.providers.base import JobSourceProvider


class LeverProvider(JobSourceProvider):
    source_name = "lever"

    def __init__(self, boards: list[str]) -> None:
        self.boards = boards

    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        for board in self.boards:
            response = httpx.get(board, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            company = urlparse(board).path.strip("/").split("/")[-1] or "unknown"
            for posting in soup.select("[class*=posting]"):
                title_el = posting.select_one("[class*=posting-title], [data-qa=posting-name]")
                link_el = posting.select_one("a[href]")
                meta_el = posting.select_one("[class*=posting-categories], [class*=posting-category]")
                if not title_el or not link_el:
                    continue
                title = title_el.get_text(" ", strip=True)
                location = meta_el.get_text(" ", strip=True) if meta_el else "Unknown"
                href = link_el.get("href", "")
                job_url = href if href.startswith("http") else f"https://jobs.lever.co{href}"
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
