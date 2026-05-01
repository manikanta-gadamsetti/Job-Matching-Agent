from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx

from job_agent.models import JobPosting, SearchConfig
from job_agent.providers.base import JobSourceProvider

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobMatchingAgent/0.1; +https://github.com/manikanta-gadamsetti/Job-Matching-Agent)"
}


class GreenhouseProvider(JobSourceProvider):
    source_name = "greenhouse"

    def __init__(self, boards: list[str]) -> None:
        self.boards = boards

    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        for board in self.boards:
            board_token = _extract_board_token(board)
            if not board_token:
                continue

            api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
            response = httpx.get(api_url, headers=HTTP_HEADERS, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("jobs", []):
                title = item.get("title", "").strip()
                location = _extract_location(item)
                job_url = item.get("absolute_url", "")
                if not title or not job_url:
                    continue
                if not _matches_search(title, location, search):
                    continue
                jobs.append(
                    JobPosting(
                        source=self.source_name,
                        title=title,
                        company=board_token.replace("_", " ").title(),
                        location=location,
                        url=job_url,
                        description=_fetch_description(board_token, item.get("id")),
                        remote="remote" in location.lower(),
                    )
                )
                if len(jobs) >= search.max_jobs_per_source:
                    break
        return jobs


def _fetch_description(board_token: str, job_id: int | None) -> str:
    if not job_id:
        return ""
    detail_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"
    response = httpx.get(detail_url, headers=HTTP_HEADERS, timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    content = payload.get("content", "")
    metadata = payload.get("metadata", [])
    metadata_text = " ".join(f"{field.get('name', '')}: {field.get('value', '')}" for field in metadata)
    body = f"{content}\n{metadata_text}"
    return body[:15000]


def _matches_search(title: str, location: str, search: SearchConfig) -> bool:
    title_l = title.lower()
    location_l = location.lower()
    title_match = any(keyword.lower() in title_l for keyword in search.keywords)
    location_match = any(loc.lower() in location_l for loc in search.locations) or "remote" in location_l
    return title_match and location_match


def _extract_board_token(board_url: str) -> str:
    parsed = urlparse(board_url)
    query = parse_qs(parsed.query)
    if "for" in query and query["for"]:
        return query["for"][0]
    path_parts = [part for part in parsed.path.split("/") if part]
    return path_parts[-1] if path_parts else ""


def _extract_location(item: dict) -> str:
    location = item.get("location") or {}
    if isinstance(location, dict):
        return location.get("name", "Unknown") or "Unknown"
    if isinstance(location, str):
        return location or "Unknown"
    offices = item.get("offices", [])
    if offices:
        office = offices[0]
        if isinstance(office, dict):
            return office.get("name", "Unknown") or "Unknown"
    return "Unknown"
