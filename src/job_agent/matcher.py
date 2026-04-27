from __future__ import annotations

from job_agent.models import CandidateProfile, JobPosting, SearchConfig


def score_job(job: JobPosting, profile: CandidateProfile, search: SearchConfig) -> JobPosting:
    haystack = " ".join(
        [
            job.title.lower(),
            job.company.lower(),
            job.location.lower(),
            job.description.lower(),
        ]
    )

    matched_keywords: list[str] = []
    score = 0.0

    for role in profile.target_roles:
        if role.lower() in haystack:
            matched_keywords.append(role)
            score += 3.0

    for keyword in search.keywords:
        if keyword.lower() in haystack and keyword not in matched_keywords:
            matched_keywords.append(keyword)
            score += 2.0

    for cert in profile.certifications:
        if cert.lower().split()[0] in haystack:
            score += 1.0

    if any(location.lower() in haystack for location in profile.preferred_locations):
        score += 2.0

    if any(token in haystack for token in ["fresher", "entry level", "junior", "graduate"]):
        score += 2.0

    if any(token in haystack for token in ["2 years", "3 years", "4 years", "senior", "lead", "manager"]):
        score -= 3.0

    if search.remote_only and not job.remote:
        score -= 5.0

    job.score = score
    job.matched_keywords = matched_keywords
    return job
