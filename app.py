"""Student-friendly entry point for the AgentForge workshop app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    """Load local settings and start the browser app."""
    load_dotenv(ROOT / ".env", override=False)
    port = int(os.getenv("AGENTFORGE_PORT", "8787"))
    uvicorn.run(
        "agentforge_jarvis.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=port,
        proxy_headers=False,
        timeout_graceful_shutdown=150,
    )


if __name__ == "__main__":
    main()
