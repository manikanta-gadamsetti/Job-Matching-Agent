from __future__ import annotations

from html import escape

from job_agent.models import JobDigest, JobPosting


def build_digest(candidate_name: str, jobs: list[JobPosting]) -> JobDigest:
    lines = [f"Hi {candidate_name},", "", "Here are your latest matching jobs:"]
    html_items: list[str] = []

    for idx, job in enumerate(jobs, start=1):
        lines.append(
            f"{idx}. {job.title} at {job.company} | {job.location} | score {job.score:.1f} | {job.url}"
        )
        html_items.append(
            "<li>"
            f"<strong>{escape(job.title)}</strong> at {escape(job.company)}"
            f" - {escape(job.location)}"
            f" - score {job.score:.1f}"
            f' - <a href="{escape(job.url)}">Open job</a>'
            "</li>"
        )

    lines.append("")
    lines.append("This digest includes only new jobs not sent before.")

    html = (
        f"<p>Hi {escape(candidate_name)},</p>"
        "<p>Here are your latest matching jobs:</p>"
        f"<ol>{''.join(html_items)}</ol>"
        "<p>This digest includes only new jobs not sent before.</p>"
    )
    return JobDigest(generated_for=candidate_name, jobs=jobs, message_text="\n".join(lines), message_html=html)
