"""Load the six student-editable agent instruction files."""

from __future__ import annotations

import os
from pathlib import Path

from .catalog import AGENTS


def prompt_directory() -> Path:
    """Return the configured prompt folder, defaulting to ``repo/agents``."""
    configured = os.getenv("AGENTFORGE_AGENT_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "agents"


def load_agent_prompt(domain: str) -> str:
    """Read one agent file and fail clearly when a student renamed it incorrectly."""
    try:
        filename = AGENTS[domain]["prompt_file"]
    except KeyError as error:
        raise ValueError(f"Unknown agent domain: {domain}") from error

    path = prompt_directory() / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing agent instructions: {path}. Keep all six files in the agents folder."
        )
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Agent instructions are empty: {path}")
    return prompt


def validate_agent_prompts() -> list[Path]:
    """Load every prompt once and return the six resolved paths."""
    directory = prompt_directory()
    paths = []
    for domain, spec in AGENTS.items():
        load_agent_prompt(domain)
        paths.append(directory / spec["prompt_file"])
    return paths
