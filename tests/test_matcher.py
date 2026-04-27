from pathlib import Path

from job_agent.filters import extract_experience_years, is_entry_level_job
from job_agent.matcher import score_job
from job_agent.models import CandidateProfile, JobPosting, SearchConfig


def test_score_job_prefers_target_role_and_location() -> None:
    profile = CandidateProfile(
        candidate_name="Test User",
        email="test@example.com",
        phone="123",
        total_experience_years=1,
        target_roles=["DevOps Engineer"],
        preferred_locations=["Hyderabad"],
        certifications=["Azure Data Engineering"],
        experience_highlights=[],
        base_resume_path=Path("resume.md"),
    )
    search = SearchConfig(keywords=["DevOps Engineer"], locations=["Hyderabad"])
    job = JobPosting(
        source="test",
        title="DevOps Engineer",
        company="Acme",
        location="Hyderabad",
        url="https://example.com/job",
        description="Azure experience preferred",
    )

    scored = score_job(job, profile, search)
    assert scored.score >= 7
    assert "DevOps Engineer" in scored.matched_keywords


def test_extract_experience_years_handles_range() -> None:
    assert extract_experience_years("Looking for engineers with 0-1 years of experience") == 1


def test_is_entry_level_job_rejects_senior_requirement() -> None:
    search = SearchConfig(keywords=["DevOps Engineer"], locations=["Hyderabad"], max_experience_years=1)
    job = JobPosting(
        source="test",
        title="DevOps Engineer",
        company="Acme",
        location="Hyderabad",
        url="https://example.com/senior-job",
        description="Requires 3 years of experience with AWS and Kubernetes",
    )
    assert is_entry_level_job(job, search) is False
