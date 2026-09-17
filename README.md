# AgentForge / JARVIS

**Six minds. One mission.** A JARVIS-styled command center: six LangChain specialists, a LangChain command assistant, and a LangGraph company-launch workflow — running on Ollama or OpenAI.

## Student quick start (recommended for the workshop)

Prerequisites: Python 3.11–3.13, Git, and Ollama with the class-approved model already downloaded.

### macOS / Linux

```sh
git clone https://github.com/arthi-rajendran24/liba-workshop-02.git
cd liba-workshop-02
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
ollama serve
```

Keep `ollama serve` running. In a **second terminal**, return to the repo, activate the environment, and launch:

```sh
cd liba-workshop-02
source .venv/bin/activate
python app.py
```

### Windows PowerShell

```powershell
git clone https://github.com/arthi-rajendran24/liba-workshop-02.git
cd liba-workshop-02
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama serve
```

Keep `ollama serve` running. In a **second PowerShell window**, return to the repo, activate the environment, and launch:

```powershell
cd liba-workshop-02
.\.venv\Scripts\Activate.ps1
python app.py
```

Open **http://127.0.0.1:8787**. If the class uses a different Ollama model, change only `AGENTFORGE_MODEL` in `.env` to the exact installed tag shown by `ollama list`.

### Optional OpenAI route

In `.env`, comment out the two active Ollama lines and enable:

```dotenv
AGENTFORGE_PROVIDER=openai
AGENTFORGE_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-own-key
```

Never paste an API key into source code, screenshots, chat, or a committed file. Restart `python app.py` after editing `.env`. Ollama and OpenAI can also be switched from the app's Settings dialog once both are configured.

## Alternative uv start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone the repository, then run all commands inside the folder containing `pyproject.toml`:

```sh
git clone https://github.com/arthi-rajendran24/liba-workshop-02.git
cd liba-workshop-02
uv sync --frozen
```

Copy `.env.example` to `.env` (`cp` on macOS/Linux, `Copy-Item` in PowerShell) and set one live provider:

```dotenv
AGENTFORGE_PROVIDER=openai
AGENTFORGE_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-own-key
```

Or run fully local with [Ollama](https://ollama.com) (no key needed — start Ollama and use the exact class-approved tag shown by `ollama list`):

```dotenv
AGENTFORGE_PROVIDER=ollama
AGENTFORGE_MODEL=gemma4:e2b
```

Then run:

```sh
uv run agentforge-jarvis web
```

JARVIS announces itself with a spoken project-status briefing as soon as the UI loads. The app needs no Node.js build, GPU, or database server.

Quick-start scripts are included: `./start.sh` (macOS/Linux) and `start.bat` (Windows) run `uv sync` and launch the server in one step.

## The six agents

| Agent | Specialization | Working tool and output |
|---|---|---|
| **PRISM** | Analytics | `analyze_signals`: channel denominators, weighted sentiment change, descriptive Wilson interval, KPI recommendations |
| **PULSE** | Marketing | `plan_marketing`: trend/sentiment hand-off, exact budget allocation, labelled campaign drafts, trust review |
| **NOVA** | HR | `screen_skills`: anonymous skills coverage, work-sample worksheet, staffing gap and cost; human review throughout |
| **ATLAS** | Operations | `assess_supply`: lead time, production capacity, shortfall, delivery buffer and fallback |
| **LEDGER** | Finance | `model_finances`: upfront cash needs, margin, break-even, downside/base/upside cases constrained by delivery capacity |
| **JARVIS** | General Management | `synthesize_strategy`: reconcile five reports, preserve hold gates, assign owners and produce the executive package |

The additional JARVIS **command interface** is a LangChain agent that can consult specialists, retrieve team notes and read the latest saved run. It is separate from the General Management synthesis agent.

## Replace the six agent instructions

The student-editable prompts are in [`agents/`](agents/README.md). Keep the filenames unchanged, replace their contents with the six agent files created on Day 1, and run the same scenario again. The app reads a file when that agent starts, so the next run uses the saved change. This makes the behavior comparison visible without asking students to edit the orchestration code.

## Working features

- Run the complete team or one specialist with its dependencies; inspect live tool events, calculations and model prose on an animated JARVIS HUD.
- Apply budget, supplier, trust or demand shocks; edit/import validated scenario JSON; compare and export saved runs.
- Switch the live model between Ollama and OpenAI at runtime from the Settings dialog — no restart required.
- Save source notes and retrieve bounded keyword-matched excerpts with citations. Team/agent conversations and blueprints persist in SQLite.
- Send a selected PNG/JPEG under 2 MB to OpenAI for text extraction, review it, then explicitly save the note.
- Browser voice transcription and read-aloud, including an optional "always listen for Jarvis" wake-word mode; review recognized text before sending (except in wake mode, which sends immediately).
- Record human scores using a 25/25/20/15/15 rubric and include the reflection in exports.

## Service controls

Authentication is available for local use and required in production mode. Team access codes are PBKDF2-hashed; random server sessions are hashed and expire after twelve hours. Signed-in requests cannot select another team's records. Production cookies are Secure, HttpOnly and SameSite=Strict. Host allowlists, same-origin checks, input limits and request limits apply.

The server admits one active request per team, two executing saved runs, eight run slots including queued work, and two concurrent chats/image requests. Provider requests have timeouts and limited retries. Reports persist after each specialist; restart recovery marks incomplete runs interrupted. Missing required tools receive one correction turn. Errors stay explicit and redacted; there is no silent fallback to simulation. Cancellation takes effect between active calls. Usage fields record reported input/output/total tokens, not invoiced cost.

`/api/health` checks the service; `/api/ready` checks storage and requires a successful live response since this process started. Readiness is observed state, not a continuous provider guarantee.

## Host and operate

Use [deploy/README.md](deploy/README.md) for team provisioning, a non-root Docker/Caddy HTTPS recipe, backup and restore. Local loopback mode leaves authentication optional; team IDs alone are workspace labels in that mode. Hosted mode forces authentication and explicit host validation.

```sh
uv run agentforge-jarvis provision-team liba-team-01 --output .agentforge/team-01-access.txt
uv run agentforge-jarvis backup .agentforge/workshop-backup.sqlite3
```

Both commands create new private files without overwriting. Re-provisioning rotates the team's code and revokes sessions. The database is `.agentforge/agentforge.sqlite3`; keep it and backups private. Run **one app process** against a database.

## Architecture

```text
Local browser HUD + optional speech
          │ same-origin HTTP / SSE
FastAPI + SQLite team workspace
          │
LangGraph workflow (dependency-ordered, sequential)
          PRISM
            ↓
    PULSE → NOVA → ATLAS
            ↓
          LEDGER
            ↓
          JARVIS → executive package + human review
```

PULSE, NOVA and ATLAS all receive PRISM's report. LEDGER receives Marketing, HR and Operations reports. General Management receives all five specialist reports. Execution is sequential to keep traces and local resource use predictable; the three specialists do not depend on each other. Two saved runs can execute at once; the queue holds at most eight submitted runs. Agent loops have bounded graph steps and tool calls; provider requests have timeouts. Cancellation takes effect between calls after any active model call returns.

Every domain is constructed with **`langchain.agents.create_agent`**, a role prompt, mandatory `read_brief` and domain tools, plus optional `search_memory` when relevant notes exist. The command assistant uses the LangChain agent-as-tool pattern. Model instances and transcripts are scoped to each invocation; stored conversation history is scoped to team and agent.

```text
app.py                         simple student launch file
requirements.txt              packages for pip installation
agents/                        six replaceable Markdown instructions
src/agentforge_jarvis/
  catalog.py      names, capabilities, rubric
  models.py       validated scenarios and report schemas
  business.py     six auditable business calculations
  providers.py    rehearsal / Ollama / OpenAI adapters, runtime provider switching
  engine.py       LangChain agents, LangGraph orchestration, exports
  storage.py      team-scoped SQLite persistence
  app.py          local HTTP API, event stream and input boundaries
  static/         JARVIS HUD (canvas neuron network, chat, mission control) — no CDN dependencies
```

The shortest code-reading path is:

1. `app.py` starts the local server.
2. `catalog.py` defines the six roles and their order.
3. `agent_prompts.py` reads the six Markdown instruction files.
4. `providers.py` chooses Ollama or OpenAI.
5. `engine.py` creates each LangChain agent and connects the LangGraph hand-offs.
6. `business.py` contains the deterministic tools/calculations.
7. `app.py` inside the package exposes the HTTP API; `static/` contains the existing UI and browser voice controls.

## Explicit rehearsal fallback

Set `AGENTFORGE_PROVIDER=rehearsal` and restart only when selecting that route. Rehearsal executes the real tools through a scripted LangChain model; it cannot interpret arbitrary instructions. The provider label makes this distinction visible.

## Scope and references

Financial scenarios, candidate worksheets and campaign drafts are fictional decision-support exercises. Human review owns launch, hiring, purchasing and publication decisions. Memory is bounded keyword retrieval, not a vector database.

The HUD, command channel and Memory Vault were inspired by [vibe-jarvis](https://github.com/arthi-rajendran24/vibe-jarvis). The implementation uses [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [OpenAI](https://platform.openai.com/docs), and [Ollama](https://ollama.com).
