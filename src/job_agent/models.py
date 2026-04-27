from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    candidate_name: str
    email: str
    phone: str
    total_experience_years: int = 0
    target_roles: list[str]
    preferred_locations: list[str]
    certifications: list[str] = Field(default_factory=list)
    experience_highlights: list[str] = Field(default_factory=list)
    base_resume_path: Path


class SearchConfig(BaseModel):
    keywords: list[str]
    locations: list[str]
    remote_only: bool = False
    max_experience_years: int = 1
    include_freshers: bool = True
    max_jobs_per_source: int = 20


class LLMConfig(BaseModel):
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2


class SourceBoardConfig(BaseModel):
    enabled: bool = False
    boards: list[str] = Field(default_factory=list)
    note: str | None = None


class AutomationConfig(BaseModel):
    browser_headless: bool = False
    storage_state_path: Path
    require_human_review_before_submit: bool = True
    auto_submit_safe_forms: bool = False


class EmailNotificationConfig(BaseModel):
    enabled: bool = False
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password_env: str
    from_address: str
    to_addresses: list[str] = Field(default_factory=list)


class WhatsAppNotificationConfig(BaseModel):
    enabled: bool = False
    provider: Literal["twilio"] = "twilio"
    account_sid_env: str
    auth_token_env: str
    from_number: str
    to_numbers: list[str] = Field(default_factory=list)


class NotificationConfig(BaseModel):
    email: EmailNotificationConfig
    whatsapp: WhatsAppNotificationConfig


class AppConfig(BaseModel):
    profile: CandidateProfile
    search: SearchConfig
    llm: LLMConfig
    sources: dict[str, SourceBoardConfig]
    automation: AutomationConfig
    notifications: NotificationConfig


class JobPosting(BaseModel):
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str
    employment_type: str | None = None
    remote: bool = False
    score: float = 0.0
    matched_keywords: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    discovered_via: str | None = None


class TailoredResume(BaseModel):
    job_url: str
    company: str
    role: str
    markdown: str
    output_path: Path


class ApplicationOutcome(BaseModel):
    job_url: str
    status: Literal["skipped", "review_required", "submitted", "failed"]
    notes: str


class JobDigest(BaseModel):
    generated_for: str
    jobs: list[JobPosting]
    message_text: str
    message_html: str


class MatchRunResult(BaseModel):
    ranked_jobs: list[JobPosting]
    fresh_jobs: list[JobPosting]
    sent_count: int = 0
    notifications_sent: bool = False
