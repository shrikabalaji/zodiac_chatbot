"""Minimal Checkpoint 2 browser interface using the final AgentForge stack."""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .checkpoint_agent import run_checkpoint_agent

app = FastAPI(title="AgentForge cumulative checkpoint")


class CheckpointRequest(BaseModel):
    domain: str = Field(pattern="^(analytics|marketing|hr|operations|finance|general-management)$")
    payload: dict
    live: bool = False


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "checkpoint": 2}


@app.post("/api/checkpoint")
def checkpoint(request: CheckpointRequest) -> dict:
    try:
        return run_checkpoint_agent(request.domain, request.payload, live=request.live)
    except (TypeError, ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    example = json.dumps(
        {"price": 120, "unit_cost": 65, "fixed_cost": 240000, "budget": 2400000},
        indent=2,
    )
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>AgentForge Checkpoint 2</title>
<style>body{{font:16px system-ui;max-width:760px;margin:40px auto;padding:0 20px}}textarea{{width:100%;height:190px}}pre{{white-space:pre-wrap;background:#f3f5f7;padding:16px}}button{{padding:10px 16px}}</style></head>
<body><h1>AgentForge Checkpoint 2</h1><p>One verified LangChain tool call using the same domain names as the complete application.</p>
<label>Domain <select id='domain'><option>finance</option><option>analytics</option><option>marketing</option><option>hr</option><option>operations</option><option>general-management</option></select></label>
<p><textarea id='payload'>{example}</textarea></p><label><input id='live' type='checkbox'> Use one live Gemini request</label>
<p><button onclick='run()'>Run agent</button></p><pre id='out'>Ready.</pre>
<script>async function run(){{let out=document.getElementById('out');try{{let response=await fetch('/api/checkpoint',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{domain:document.getElementById('domain').value,payload:JSON.parse(document.getElementById('payload').value),live:document.getElementById('live').checked}})}});out.textContent=JSON.stringify(await response.json(),null,2)}}catch(error){{out.textContent=String(error)}}}}</script></body></html>"""
