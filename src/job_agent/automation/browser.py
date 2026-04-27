from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, TimeoutError, sync_playwright

from job_agent.models import ApplicationOutcome, AutomationConfig, CandidateProfile, JobPosting, TailoredResume


class BrowserApplicator:
    def __init__(self, config: AutomationConfig) -> None:
        self.config = config
        self.config.storage_state_path.parent.mkdir(parents=True, exist_ok=True)

    def run(self, jobs: list[JobPosting], profile: CandidateProfile, resumes: dict[str, TailoredResume]) -> list[ApplicationOutcome]:
        outcomes: list[ApplicationOutcome] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.config.browser_headless)
            context = browser.new_context(
                storage_state=str(self.config.storage_state_path) if self.config.storage_state_path.exists() else None
            )
            page = context.new_page()

            for job in jobs:
                resume = resumes.get(str(job.url))
                outcomes.append(self._apply_to_job(page, job, profile, resume))

            context.storage_state(path=str(self.config.storage_state_path))
            browser.close()
        return outcomes

    def _apply_to_job(
        self,
        page: Page,
        job: JobPosting,
        profile: CandidateProfile,
        resume: TailoredResume | None,
    ) -> ApplicationOutcome:
        try:
            page.goto(str(job.url), wait_until="domcontentloaded", timeout=45_000)
        except TimeoutError:
            return ApplicationOutcome(job_url=str(job.url), status="failed", notes="Navigation timed out.")

        if _looks_like_login_or_challenge(page):
            return ApplicationOutcome(
                job_url=str(job.url),
                status="review_required",
                notes="Manual login, MFA, or CAPTCHA is required.",
            )

        # Fill only common low-risk fields. Anything ambiguous is left for the user.
        _fill_if_present(page, 'input[name*="name" i]', profile.candidate_name)
        _fill_if_present(page, 'input[type="email"]', profile.email)
        _fill_if_present(page, 'input[type="tel"], input[name*="phone" i]', profile.phone)

        if resume:
            _fill_if_present(page, 'textarea[name*="cover" i]', _build_cover_note(job, profile))

        if self.config.require_human_review_before_submit:
            return ApplicationOutcome(
                job_url=str(job.url),
                status="review_required",
                notes=f"Form filled where possible. Review tailored resume at {resume.output_path if resume else 'N/A'} before submitting.",
            )

        return ApplicationOutcome(
            job_url=str(job.url),
            status="skipped",
            notes="Auto-submit disabled by default for safety.",
        )


def _fill_if_present(page: Page, selector: str, value: str) -> None:
    locator = page.locator(selector).first
    if locator.count():
        locator.fill(value)


def _looks_like_login_or_challenge(page: Page) -> bool:
    text = page.locator("body").inner_text(timeout=3_000).lower()
    markers = ["captcha", "sign in", "log in", "verify you are", "two-factor", "mfa"]
    return any(marker in text for marker in markers)


def _build_cover_note(job: JobPosting, profile: CandidateProfile) -> str:
    highlights = "; ".join(profile.experience_highlights[:2])
    return f"Interested in the {job.title} role. Relevant background: {highlights}."
