from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from job_agent.models import CandidateProfile, JobPosting, TailoredResume


def tailor_resume(
    client: OpenAI,
    model: str,
    prompt_path: Path,
    base_resume_markdown: str,
    profile: CandidateProfile,
    job: JobPosting,
    output_dir: Path,
) -> TailoredResume:
    system_prompt = prompt_path.read_text(encoding="utf-8")
    user_prompt = f"""
Candidate profile:
{profile.model_dump_json(indent=2)}

Base resume:
{base_resume_markdown}

Job description:
Title: {job.title}
Company: {job.company}
Location: {job.location}
URL: {job.url}

{job.description}
"""
    response = client.responses.create(
        model=model,
        temperature=0.2,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    markdown = response.output_text.strip()
    safe_company = "".join(ch for ch in job.company.lower() if ch.isalnum() or ch in ("-", "_")).strip()
    safe_role = "".join(ch for ch in job.title.lower() if ch.isalnum() or ch in ("-", "_")).strip()
    output_path = output_dir / f"{safe_company}_{safe_role}.md"
    output_path.write_text(markdown, encoding="utf-8")
    return TailoredResume(
        job_url=str(job.url),
        company=job.company,
        role=job.title,
        markdown=markdown,
        output_path=output_path,
    )
