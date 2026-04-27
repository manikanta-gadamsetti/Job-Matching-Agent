from __future__ import annotations

from abc import ABC, abstractmethod

from job_agent.models import JobPosting, SearchConfig


class JobSourceProvider(ABC):
    source_name: str

    @abstractmethod
    def fetch_jobs(self, search: SearchConfig) -> list[JobPosting]:
        raise NotImplementedError
