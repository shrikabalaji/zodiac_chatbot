FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AGENTFORGE_DATA_DIR=/data
WORKDIR /app
RUN pip install --no-cache-dir uv==0.10.2
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
RUN useradd --uid 10001 --create-home app && mkdir /data && chown app:app /data
USER app
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/api/health',timeout=4)"]
CMD ["/app/.venv/bin/agentforge-jarvis", "web", "--host", "0.0.0.0", "--port", "8787"]
