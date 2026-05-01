from __future__ import annotations

from urllib.parse import urlparse

import httpx

from job_agent.models import JobPosting, SearchConfig
from job_agent.providers.base import JobSourceProvider

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobMatchingAgent/0.1; +https://github.com/manikanta-gadamsetti/Job-Matching-Agent)"
}


class LeverProvider(JobSourceProvider):
    source_name = "lever"

    def __init__(self, boards: list[str]) -> None:
        self.boards = boards

    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        for board in self.boards:
            company = urlparse(board).path.strip("/").split("/")[-1] or "unknown"
            api_url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            response = httpx.get(api_url, headers=HTTP_HEADERS, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            payload = response.json()
            for posting in payload:
                title = posting.get("text", "").strip()
                categories = posting.get("categories", {})
                location = categories.get("location", "Unknown") if isinstance(categories, dict) else "Unknown"
                job_url = posting.get("hostedUrl", "")
                description = posting.get("descriptionPlain") or posting.get("description") or ""
                if not title or not job_url:
                    continue
                if not _matches_search(title, location, search):
                    continue
                jobs.append(
                    JobPosting(
                        source=self.source_name,
                        title=title,
                        company=company.title(),
                        location=location,
                        url=job_url,
                        description=description[:15000],
                        remote="remote" in location.lower(),
                    )
                )
                if len(jobs) >= search.max_jobs_per_source:
                    break
        return jobs


def _matches_search(title: str, location: str, search: SearchConfig) -> bool:
    title_l = title.lower()
    location_l = location.lower()
    title_match = any(keyword.lower() in title_l for keyword in search.keywords)
    location_match = any(loc.lower() in location_l for loc in search.locations) or "remote" in location_l
    return title_match and location_match
