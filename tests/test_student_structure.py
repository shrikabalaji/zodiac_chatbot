from pathlib import Path

from agentforge_jarvis.agent_prompts import load_agent_prompt, validate_agent_prompts
from agentforge_jarvis.catalog import AGENTS


def test_six_agent_files_are_present_and_non_empty():
    paths = validate_agent_prompts()
    assert len(paths) == 6
    assert all(path.is_file() and path.read_text(encoding="utf-8").strip() for path in paths)


def test_catalog_maps_one_unique_file_per_agent():
    filenames = [spec["prompt_file"] for spec in AGENTS.values()]
    assert len(filenames) == len(set(filenames)) == 6


def test_prompt_content_is_loaded_from_markdown():
    assert "PRISM" in load_agent_prompt("analytics")
    assert Path("app.py").is_file()
    assert Path("requirements.txt").is_file()


def test_zodiac_agent_catalog():
    expected = {
        "analytics": ("SCORPIO", "♏"),
        "marketing": ("PISCES", "♓"),
        "hr": ("CANCER", "♋"),
        "operations": ("ARIES", "♈"),
        "finance": ("TAURUS", "♉"),
        "general-management": ("LIBRA", "♎"),
    }
    for domain, (name, symbol) in expected.items():
        assert AGENTS[domain]["name"] == name
        assert AGENTS[domain]["symbol"] == symbol
