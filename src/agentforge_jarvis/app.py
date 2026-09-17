from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .catalog import AGENTS, CHALLENGES, RUBRIC
from .engine import Engine, export_markdown
from .models import (
    BlueprintRequest,
    ChatRequest,
    Domain,
    NoteRequest,
    RunRequest,
    Scenario,
    StrictModel,
    apply_challenge,
)
from .providers import SWITCHABLE_PROVIDERS, Settings, public_error
from .security import BusyError, RateLimiter, TeamAuth
from .storage import Store

TEAM = r"^[a-zA-Z0-9_-]{1,48}$"
STATIC = Path(__file__).parent / "static"


class Assessment(StrictModel):
    team: str = Field(pattern=TEAM)
    scores: list[int] = Field(min_length=5, max_length=5)
    reflection: str = Field(min_length=1, max_length=6000)


class ImageRequest(StrictModel):
    team: str = Field(pattern=TEAM)
    mime: Literal["image/png", "image/jpeg"]
    data: str = Field(min_length=1, max_length=2800000)


class Login(StrictModel):
    team: str = Field(pattern=TEAM)
    password: str = Field(min_length=1, max_length=256)


class ProviderSwitch(StrictModel):
    provider: Literal[*SWITCHABLE_PROVIDERS]
    model: str = Field(min_length=1, max_length=200)


def create_app(data_dir: Path | None = None, settings: Settings | None = None):
    store = Store(data_dir or Path(os.getenv("AGENTFORGE_DATA_DIR", ".agentforge")))
    engine = Engine(store, settings)
    auth = TeamAuth(store)
    production = os.getenv("AGENTFORGE_ENV") == "production"
    auth_required = production or os.getenv("AGENTFORGE_AUTH_REQUIRED", "false").lower() == "true"
    secure_cookie = production or os.getenv("AGENTFORGE_SECURE_COOKIE", "false").lower() == "true"
    hosts = os.getenv("AGENTFORGE_ALLOWED_HOSTS", "127.0.0.1,localhost,[::1],testserver").split(",")
    if production and (
        "*" in hosts or engine.settings.error() or engine.settings.provider == "rehearsal"
    ):
        raise ValueError(
            "Production requires explicit allowed hosts and a configured live provider."
        )
    login_limiter = RateLimiter(8, 60)
    work_limiter = RateLimiter(12, 60)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.close()

    app = FastAPI(title="AgentForge JARVIS", lifespan=lifespan)
    app.state.engine = engine
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != request.headers.get("host"):
            return JSONResponse(
                {"detail": "Cross-origin access is disabled for this local workspace."},
                status_code=403,
            )
        limit = 2900000 if request.url.path == "/api/media/extract" else 200000
        length = request.headers.get("content-length", "0")
        if not length.isdigit() or int(length) > limit:
            return JSONResponse(
                {"detail": "Request exceeds the input size limit."}, status_code=413
            )
        # Count streamed bodies too; Content-Length alone is not sufficient for chunked requests.
        if request.method in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > limit:
                    return JSONResponse(
                        {"detail": "Request exceeds the input size limit."}, status_code=413
                    )
            request._body = bytes(body)
        path = request.url.path
        team = auth.team(request.cookies.get(TeamAuth.COOKIE)) if auth_required else None
        if (
            auth_required
            and path.startswith("/api/")
            and path
            not in {"/api/health", "/api/auth/status", "/api/auth/login", "/api/auth/logout"}
        ):
            if not team:
                return JSONResponse({"detail": "Sign in to your team workspace."}, status_code=401)
            requested = request.query_params.get("team")
            if request.method in {"POST", "PUT", "PATCH"} and path not in {
                "/api/scenario/validate",
                "/api/settings",
            }:
                try:
                    payload = json.loads(await request.body())
                    requested = (
                        payload.get("team", "liba-team-01") if isinstance(payload, dict) else None
                    )
                except (ValueError, UnicodeDecodeError):
                    return JSONResponse({"detail": "Invalid JSON."}, status_code=400)
            if requested and requested != team:
                return JSONResponse(
                    {"detail": "This session cannot access another team's workspace."},
                    status_code=403,
                )
            if path == "/api/bootstrap" and not requested and team != "liba-team-01":
                return JSONResponse({"detail": "Provide your signed-in team ID."}, status_code=403)
        if request.method == "POST" and path in {"/api/runs", "/api/chat", "/api/media/extract"}:
            key = team or (request.client.host if request.client else "local")
            if not work_limiter.allow(key):
                return JSONResponse(
                    {"detail": "Request rate limit reached. Retry in a minute."},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(BusyError)
    async def busy_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=429, headers={"Retry-After": "10"})

    @app.get("/api/auth/status")
    def auth_status(request: Request):
        return {
            "required": auth_required,
            "team": auth.team(request.cookies.get(TeamAuth.COOKIE)) if auth_required else None,
        }

    @app.post("/api/auth/login")
    def login(payload: Login, request: Request):
        key = request.client.host if request.client else "unknown"
        if not login_limiter.allow(key):
            raise HTTPException(429, "Too many sign-in attempts. Wait one minute.")
        token = auth.login(payload.team, payload.password)
        if not token:
            raise HTTPException(401, "Team ID or access code is incorrect.")
        response = JSONResponse({"team": payload.team})
        response.set_cookie(
            TeamAuth.COOKIE,
            token,
            httponly=True,
            secure=secure_cookie,
            samesite="strict",
            max_age=TeamAuth.TTL,
        )
        return response

    @app.post("/api/auth/logout")
    def logout(request: Request):
        auth.logout(request.cookies.get(TeamAuth.COOKIE))
        response = JSONResponse({"signed_out": True})
        response.delete_cookie(TeamAuth.COOKIE)
        return response

    @app.get("/api/ready")
    def ready():
        status = engine.public_status()
        with store.connection() as db:
            db.execute("SELECT 1")
        ok = status["configured"] and (
            engine.settings.provider == "rehearsal" or status["live_verified"]
        )
        return JSONResponse({"ready": ok, **status}, status_code=200 if ok else 503)

    @app.exception_handler(ValueError)
    async def value_error(request, error):
        # Input/configuration errors generated by this app have no credential content.
        return JSONResponse({"detail": str(error)}, status_code=400)

    def find_run(run_id: str, team: str):
        run = store.get_run(run_id, team)
        if not run:
            raise HTTPException(404, "Run not found in this team's workspace.")
        return run

    @app.get("/api/health")
    def health():
        return {"status": "ok", **engine.public_status()}

    @app.post("/api/settings")
    def switch_provider(payload: ProviderSwitch):
        return engine.switch_provider(payload.provider, payload.model)

    @app.get("/api/bootstrap")
    def bootstrap(team: str = Query(default="liba-team-01", pattern=TEAM)):
        return {
            "agents": [
                {"id": d, **spec, "instructions": store.blueprint(team, d)}
                for d, spec in AGENTS.items()
            ],
            "scenario": Scenario().model_dump(),
            "challenges": CHALLENGES,
            "rubric": RUBRIC,
            "settings": engine.public_status(),
            "runs": store.runs(team),
            "notes": store.notes(team),
            "messages": store.messages(team, "supervisor", 40),
        }

    @app.post("/api/scenario/validate")
    def validate_scenario(payload: Scenario):
        return apply_challenge(payload, "baseline").model_dump()

    @app.post("/api/runs", status_code=202)
    def start_run(payload: RunRequest):
        return engine.start_run(payload)

    @app.get("/api/runs")
    def runs(team: str = Query(pattern=TEAM)):
        return store.runs(team)

    @app.get("/api/runs/{run_id}")
    def run(run_id: str, team: str = Query(pattern=TEAM)):
        return find_run(run_id, team)

    @app.post("/api/runs/{run_id}/cancel")
    def cancel(run_id: str, team: str = Query(pattern=TEAM)):
        run = find_run(run_id, team)
        engine.cancel(run_id)
        return {"requested": run["status"] in {"queued", "running"}}

    @app.get("/api/runs/{run_id}/events")
    async def events(
        run_id: str, request: Request, team: str = Query(pattern=TEAM), after: int = 0
    ):
        find_run(run_id, team)
        try:
            cursor = max(after, int(request.headers.get("last-event-id", "0")))
        except ValueError:
            cursor = max(0, after)

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                for event in store.events(run_id, cursor):
                    cursor = event["id"]
                    yield f"id: {cursor}\ndata: {json.dumps(event)}\n\n"
                current = store.get_run(run_id, team)
                if current and current["status"] not in {"running", "queued"}:
                    yield f"event: done\ndata: {json.dumps({'status': current['status']})}\n\n"
                    break
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.3)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/api/runs/{run_id}/export")
    def export(run_id: str, team: str = Query(pattern=TEAM), format: Literal["md", "json"] = "md"):
        run = find_run(run_id, team)
        if run["status"] != "completed":
            raise HTTPException(409, "Only completed runs have an executive package.")
        content = export_markdown(run) if format == "md" else json.dumps(run, indent=2)
        return Response(
            content,
            media_type="text/markdown" if format == "md" else "application/json",
            headers={
                "Content-Disposition": f'attachment; filename="agentforge-{run_id[:8]}.{format}"'
            },
        )

    @app.post("/api/runs/{run_id}/assessment")
    def assess(run_id: str, payload: Assessment):
        run = find_run(run_id, payload.team)
        if run["status"] != "completed":
            raise HTTPException(409, "Complete the run before assessment.")
        if any(score < 0 or score > 5 for score in payload.scores):
            raise ValueError("Each rubric score must be between 0 and 5.")
        run["assessment"] = {
            "scores": payload.scores,
            "reflection": payload.reflection,
            "weighted_total": sum(
                score / 5 * item["weight"]
                for score, item in zip(payload.scores, RUBRIC, strict=True)
            ),
            "rubric": RUBRIC,
            "scored_by": "Human facilitator or team self-assessment",
        }
        store.put_run(run)
        return run["assessment"]

    @app.post("/api/chat")
    def chat(payload: ChatRequest):
        try:
            return engine.chat(payload)
        except BusyError:
            raise
        except ValueError as error:
            if engine.settings.error():
                raise ValueError(engine.settings.error()) from error
            raise HTTPException(
                502,
                public_error(error),
            ) from error
        except Exception as error:
            raise HTTPException(
                502,
                public_error(error),
            ) from error

    @app.post("/api/media/extract")
    def media(payload: ImageRequest):
        from .media import extract_image

        try:
            return {
                "text": extract_image(engine, payload.team, payload.data, payload.mime),
                "saved": False,
            }
        except ValueError:
            raise
        except Exception as error:
            raise HTTPException(502, public_error(error)) from error

    @app.get("/api/messages")
    def messages(team: str = Query(pattern=TEAM), domain: str = "supervisor"):
        if domain != "supervisor" and domain not in AGENTS:
            raise HTTPException(404, "Unknown agent")
        return store.messages(team, domain, 40)

    @app.post("/api/notes", status_code=201)
    def note(payload: NoteRequest):
        if len(store.notes(payload.team)) >= 50:
            raise ValueError("The local lab allows 50 notes per team. Remove an old note first.")
        return store.add_note(payload.team, payload.title, payload.text)

    @app.delete("/api/notes/{note_id}")
    def delete_note(note_id: str, team: str = Query(pattern=TEAM)):
        store.delete_note(team, note_id)
        return {"deleted": True}

    @app.put("/api/agents/{domain}/blueprint")
    def blueprint(domain: Domain, payload: BlueprintRequest):
        store.set_blueprint(payload.team, domain, payload.instructions)
        return {"saved": True}

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
