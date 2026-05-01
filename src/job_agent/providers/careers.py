from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from job_agent.models import JobPosting, SearchConfig
from job_agent.providers.base import JobSourceProvider


class CareersPageProvider(JobSourceProvider):
    source_name = "careers"

    def __init__(self, pages: list[str]) -> None:
        self.pages = pages

    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        for page_url in self.pages:
            try:
                response = httpx.get(
                    page_url,
                    timeout=20.0,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; JobMatchingAgent/0.1; +https://github.com/manikanta-gadamsetti/Job-Matching-Agent)"
                    },
                )
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            company = urlparse(page_url).netloc.replace("www.", "")
            for link in soup.select("a[href]"):
                title = link.get_text(" ", strip=True)
                href = link.get("href", "")
                if not _looks_like_job_link(title, href):
                    continue
                job_url = urljoin(page_url, href)
                if not _matches_search(title, "", search):
                    continue
                jobs.append(
                    JobPosting(
                        source=self.source_name,
                        title=title,
                        company=company,
                        location="Unknown",
                        url=job_url,
                        description=f"Discovered from {page_url}",
                        discovered_via=page_url,
                    )
                )
                if len(jobs) >= search.max_jobs_per_source:
                    break
        return jobs


def _looks_like_job_link(title: str, href: str) -> bool:
    joined = f"{title} {href}".lower()
    tokens = ["job", "career", "opening", "position", "apply", "requisition"]
    return any(token in joined for token in tokens)


def _matches_search(title: str, location: str, search: SearchConfig) -> bool:
    title_l = title.lower()
    location_l = location.lower()
    title_match = any(keyword.lower() in title_l for keyword in search.keywords)
    location_match = not location or any(loc.lower() in location_l for loc in search.locations) or "remote" in location_l
    return title_match and location_match
