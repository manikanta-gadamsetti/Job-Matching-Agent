from __future__ import annotations

import typer

from job_agent.config import load_config
from job_agent.pipeline import run_pipeline

app = typer.Typer(help="Semi-autonomous job application agent")


@app.command()
def run() -> None:
    env, config = load_config()
    run_pipeline(env.openai_api_key, config)


if __name__ == "__main__":
    app()
