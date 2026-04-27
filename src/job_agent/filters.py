from __future__ import annotations

import re

from job_agent.models import JobPosting, SearchConfig

EXPERIENCE_PATTERNS = [
    re.compile(r"\b(\d+)\s*[-–to]+\s*(\d+)\s+years?\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\+?\s+years?\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s*yrs?\b", re.IGNORECASE),
]


def extract_experience_years(text: str) -> int | None:
    for pattern in EXPERIENCE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        if len(match.groups()) == 2:
            return int(match.group(2))
        return int(match.group(1))
    return 0 if "fresher" in text.lower() else None


def is_entry_level_job(job: JobPosting, search: SearchConfig) -> bool:
    text = " ".join([job.title, job.description, job.location])
    years = extract_experience_years(text)
    job.experience_years = years
    if years is None:
        return True
    if years == 0:
        return search.include_freshers
    return years <= search.max_experience_years
