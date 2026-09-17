#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
uv sync --frozen
exec uv run agentforge-jarvis web "$@"
