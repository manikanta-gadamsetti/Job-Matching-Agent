from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx

from job_agent.models import CandidateProfile, JobPosting, SearchConfig
from job_agent.providers.base import JobSourceProvider


class SerpApiProvider(JobSourceProvider):
    source_name = "serpapi"

    def __init__(self, site_hints: list[str], profile: CandidateProfile) -> None:
        self.site_hints = site_hints
        self.profile = profile

    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        api_key = os.environ.get("SERPAPI_API_KEY", "")
        if not api_key:
            return []

        queries = []
        for role in self.profile.target_roles:
            for location in search.locations:
                queries.append(f'{role} {location} "0-1 years" jobs')
                queries.append(f'{role} {location} fresher jobs')

        jobs: list[JobPosting] = []
        for query in queries[: search.max_jobs_per_source]:
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": 10,
            }
            response = httpx.get("https://serpapi.com/search.json", params=params, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
            for result in payload.get("organic_results", []):
                link = result.get("link")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if not link or not _looks_like_job_result(link, title):
                    continue
                jobs.append(
                    JobPosting(
                        source=self.source_name,
                        title=title,
                        company=_guess_company(link),
                        location=_guess_location(snippet),
                        url=link,
                        description=snippet,
                        discovered_via=query,
                        remote="remote" in snippet.lower(),
                    )
                )
                if len(jobs) >= search.max_jobs_per_source:
                    return jobs
        return jobs


def _looks_like_job_result(link: str, title: str) -> bool:
    haystack = f"{link} {title}".lower()
    return any(token in haystack for token in ["linkedin", "naukri", "indeed", "careers", "jobs", "greenhouse", "lever"])


def _guess_company(link: str) -> str:
    host = urlparse(link).netloc.replace("www.", "")
    return host.split(".")[0].title() if host else "Unknown"


def _guess_location(snippet: str) -> str:
    for location in ["hyderabad", "remote", "bangalore", "pune", "chennai", "india"]:
        if location in snippet.lower():
            return location.title()
    return "Unknown"
