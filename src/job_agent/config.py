from __future__ import annotations

from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from job_agent.models import AppConfig


class EnvSettings(BaseSettings):
    openai_api_key: str | None = None
    job_agent_config_path: str = "config.yaml"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def load_config() -> tuple[EnvSettings, AppConfig]:
    env = EnvSettings()
    config_path = Path(env.job_agent_config_path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return env, AppConfig.model_validate(raw)
