from __future__ import annotations

from openai import OpenAI


def build_openai_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)
