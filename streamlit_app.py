from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

from job_agent.config import load_config
from job_agent.pipeline import collect_matches, notify_matches
from job_agent.storage import load_sent_job_urls

CONFIG_PATH = Path("config.yaml")
SENT_PATH = Path("data/jobs/sent_jobs.json")


def main() -> None:
    st.set_page_config(
        page_title="Job Matching Agent",
        page_icon="briefcase",
        layout="wide",
    )

    st.title("Job Matching Agent")
    st.caption("Find fresher and 0-1 year roles from public job sources and send fresh matches to email or WhatsApp.")

    _, config = load_config()
    sent_count = len(load_sent_job_urls(SENT_PATH))

    col1, col2, col3 = st.columns(3)
    col1.metric("Target Roles", len(config.profile.target_roles))
    col2.metric("Preferred Locations", len(config.profile.preferred_locations))
    col3.metric("Sent Jobs", sent_count)

    with st.sidebar:
        st.header("Profile")
        candidate_name = st.text_input("Name", value=config.profile.candidate_name)
        email = st.text_input("Email", value=config.profile.email)
        phone = st.text_input("Phone", value=config.profile.phone)
        total_experience_years = st.number_input(
            "Total Experience (Years)",
            min_value=0,
            max_value=10,
            value=config.profile.total_experience_years,
            step=1,
        )
        target_roles = st.text_area("Target Roles", value="\n".join(config.profile.target_roles), height=120)
        preferred_locations = st.text_area(
            "Preferred Locations",
            value="\n".join(config.profile.preferred_locations),
            height=100,
        )
        certifications = st.text_area("Certifications", value="\n".join(config.profile.certifications), height=100)
        experience_highlights = st.text_area(
            "Experience Highlights",
            value="\n".join(config.profile.experience_highlights),
            height=120,
        )

        if st.button("Save Profile", use_container_width=True):
            raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
            raw["profile"]["candidate_name"] = candidate_name
            raw["profile"]["email"] = email
            raw["profile"]["phone"] = phone
            raw["profile"]["total_experience_years"] = int(total_experience_years)
            raw["profile"]["target_roles"] = _split_lines(target_roles)
            raw["profile"]["preferred_locations"] = _split_lines(preferred_locations)
            raw["profile"]["certifications"] = _split_lines(certifications)
            raw["profile"]["experience_highlights"] = _split_lines(experience_highlights)
            CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
            st.success("Profile saved to config.yaml")
            st.rerun()

    enabled_sources = [name for name, source in config.sources.items() if source.enabled]
    st.subheader("Enabled Sources")
    st.write(", ".join(enabled_sources) if enabled_sources else "No sources enabled.")

    if st.button("Run Matching Agent", type="primary", use_container_width=True):
        with st.spinner("Searching and ranking jobs..."):
            _, fresh_config = load_config()
            result = collect_matches(fresh_config)
            notify_matches(fresh_config, result)
        st.success(f"Found {len(result.fresh_jobs)} fresh jobs and sent {result.sent_count} notifications.")
        st.session_state["latest_jobs"] = [job.model_dump() for job in result.fresh_jobs[:20]]

    st.subheader("Latest Fresh Matches")
    latest_jobs = st.session_state.get("latest_jobs", [])
    if not latest_jobs:
        st.info("Run the agent to fetch and send fresh job matches.")
    else:
        for job in latest_jobs:
            with st.container(border=True):
                st.markdown(f"### {job['title']}")
                st.write(f"{job['company']} | {job['location']} | score {job['score']:.1f}")
                st.link_button("Open listing", job["url"])


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


if __name__ == "__main__":
    main()
