from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv(Path.cwd() / ".env", override=False)
    parser = argparse.ArgumentParser(
        description="AgentForge JARVIS · LangChain workshop command center"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    web = commands.add_parser("web", help="Start the local command center")
    web.add_argument("--port", type=int, default=8787)
    web.add_argument("--host", default="127.0.0.1")
    provision = commands.add_parser("provision-team", help="Create or rotate a team access code")
    provision.add_argument("team")
    provision.add_argument(
        "--output", type=Path, help="Write access code to a private file instead of terminal"
    )
    backup = commands.add_parser("backup", help="Create a consistent SQLite backup")
    backup.add_argument("destination", type=Path)
    commands.add_parser(
        "doctor", help="Check dependencies and provider configuration without model calls"
    )
    demo = commands.add_parser("demo", help="Run and validate all six LangChain agents")
    demo.add_argument(
        "--challenge",
        choices=["baseline", "budget-cut", "supply-delay", "sentiment-shift", "demand-surge"],
        default="baseline",
    )
    demo.add_argument(
        "--live", action="store_true", help="Use configured provider (default: rehearsal)"
    )
    args = parser.parse_args()
    from .providers import Settings

    if args.command == "web":
        import uvicorn

        from .app import create_app

        if (
            args.host not in {"127.0.0.1", "localhost", "::1"}
            and os.getenv("AGENTFORGE_ENV") != "production"
        ):
            parser.error(
                "Non-loopback binding requires AGENTFORGE_ENV=production and authenticated HTTPS deployment."
            )
        uvicorn.run(
            create_app(),
            host=args.host,
            port=args.port,
            proxy_headers=False,
            timeout_graceful_shutdown=150,
        )
    elif args.command == "provision-team":
        import re
        import secrets

        from .security import TeamAuth
        from .storage import Store

        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", args.team):
            parser.error("Use a team ID of 1–48 letters, digits, hyphens or underscores.")
        password = secrets.token_urlsafe(18)
        store = Store(Path(os.getenv("AGENTFORGE_DATA_DIR", ".agentforge")))
        if args.output:
            # Exclusive creation protects existing credentials and avoids symlink overwrites.
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as output:
                output.write(f"Team: {args.team}\nAccess code: {password}\n")
            TeamAuth(store).provision(args.team, password)
            print("Team provisioned. Private access-code file created.")
        else:
            TeamAuth(store).provision(args.team, password)
            print(
                f"Team: {args.team}\nAccess code: {password}\nKeep this code private; it is not an API key."
            )
    elif args.command == "backup":
        import sqlite3

        from .storage import Store

        store = Store(Path(os.getenv("AGENTFORGE_DATA_DIR", ".agentforge")))
        fd = os.open(args.destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with store.connection() as source, sqlite3.connect(args.destination) as target:
            source.backup(target)
        print("Consistent database backup created.")
    elif args.command == "doctor":
        from importlib.metadata import version

        settings = Settings.from_env()
        print(
            json.dumps(
                {
                    **settings.public(),
                    "langchain": version("langchain"),
                    "langgraph": version("langgraph"),
                    "data_dir": str(
                        Path(os.getenv("AGENTFORGE_DATA_DIR", ".agentforge")).resolve()
                    ),
                    "note": "Configuration check only. Live model reachability has not been tested.",
                },
                indent=2,
            )
        )
        raise SystemExit(1 if settings.error() else 0)
    elif args.command == "demo":
        import threading
        from tempfile import TemporaryDirectory

        from .engine import Engine, validate_package
        from .models import RunRequest
        from .storage import Store

        with TemporaryDirectory() as tmp:
            engine = Engine(Store(Path(tmp)), Settings.from_env() if args.live else Settings())
            try:
                reports = engine.graph(
                    RunRequest(challenge=args.challenge), lambda *a, **kw: None, threading.Event()
                )
                checks = validate_package(reports)
                print(
                    json.dumps(
                        {
                            "provider": engine.settings.provider,
                            "reports": {d: r.model_dump() for d, r in reports.items()},
                            "checks": checks,
                        },
                        indent=2,
                    )
                )
                if not all(x["passed"] for x in checks):
                    raise SystemExit(1)
            finally:
                engine.close()
