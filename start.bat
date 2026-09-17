@echo off
cd /d "%~dp0"
uv sync --frozen
if errorlevel 1 exit /b 1
uv run agentforge-jarvis web %*
