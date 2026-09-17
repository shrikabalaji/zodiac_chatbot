# LIBA Day 2 Student Quick Start

## Goal

Run the six-agent app, observe one baseline, replace all six agent instruction files with your Day 1 work, and compare the result using the same scenario.

## 1. Clone

```sh
git clone https://github.com/arthi-rajendran24/liba-workshop-02.git
cd liba-workshop-02
```

If the folder already exists, do not clone over it. Open the existing folder or ask the facilitator before changing anything.

## 2. Create and activate the environment

macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Your terminal should now show `(.venv)`.

## 3. Install

```sh
python -m pip install -r requirements.txt
```

## 4. Configure Ollama

Copy the example settings:

macOS/Linux:

```sh
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env`. Keep:

```dotenv
AGENTFORGE_PROVIDER=ollama
AGENTFORGE_MODEL=gemma4:e2b
```

Use the exact model tag approved by the facilitator. Check installed tags with:

```sh
ollama list
```

Start Ollama and leave it running:

```sh
ollama serve
```

## 5. Launch in a second terminal

Activate `.venv` again, then:

```sh
python app.py
```

Open http://127.0.0.1:8787.

## 6. Capture the baseline

1. Use the facilitator’s chosen scenario and challenge.
2. Run the complete team.
3. Watch the agent and tool events.
4. Save one screenshot.
5. Write down one hand-off you can explain.

## 7. Replace your six agent files

Open `agents/` and keep these exact filenames:

```text
01-analytics-agent.md
02-marketing-agent.md
03-hr-agent.md
04-operations-agent.md
05-finance-agent.md
06-general-management-agent.md
```

Replace the contents with the matching six files your team created on Day 1. Do not add API keys or personal data. Save all files.

## 8. Run the controlled comparison

Run the same scenario again. Capture the result and complete:

| Observation | Before | After | Why we think it changed |
|---|---|---|---|
| Output structure |  |  |  |
| Priority or risk |  |  |  |
| Agent hand-off |  |  |  |
| Tool calculation that stayed fixed |  |  |  |

## 9. Optional OpenAI route

Only if approved, edit `.env`:

```dotenv
AGENTFORGE_PROVIDER=openai
AGENTFORGE_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-own-key
```

Restart `python app.py`. Never share or commit the key.

## 10. Submit

- baseline screenshot;
- after-change screenshot;
- six Markdown files;
- completed comparison table;
- Lovable game link or screenshot and final prompt;
- one sentence stating what still needs human approval.
