# Deployment and operating guide

This application is a **single-process service** with a durable SQLite database and a bounded in-process work queue. It is suitable for a controlled workshop deployment after capacity and provider-quota rehearsal on the actual host. Do not launch multiple app workers against the same database: startup recovery and run ownership assume one process. This repository does not provision a cloud account, hostname, billing or Gemini quota.

## Local workshop path

Copy `.env.example` to `.env`, configure Gemini locally, then `uv sync --frozen` and `uv run agentforge-jarvis web`. The server binds to loopback. Participants building on their own laptops configure their own approved Gemini access; the facilitator's private key is never part of the repository.

To require sign-in even on a local demonstration, set `AGENTFORGE_AUTH_REQUIRED=true`, provision teams, then restart. Each team uses a generated access code. These codes are not model API keys.

```sh
uv run agentforge-jarvis provision-team liba-team-01 --output .agentforge/team-01-access.txt
```

The output file is created exclusively with private permissions; it will not overwrite an existing file. Re-provisioning a team rotates the code and revokes existing sessions. Distribute each code privately to that team. Do not commit these files.

## Hosted HTTPS path

Prerequisites: a Docker-capable server, an actual DNS name pointing to it, ports 80/443 available, and the required Gemini quota/billing already approved. Set `WORKSHOP_HOST` to the real DNS hostname in the shell. Keep `.env` on the host with the live provider and key; do not place keys in Compose YAML.

From the repository root:

```sh
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml run --rm app /app/.venv/bin/agentforge-jarvis provision-team liba-team-01
docker compose -f deploy/compose.yaml up -d
```

Repeat provisioning for the actual team IDs. Capture and distribute the generated codes privately. Caddy obtains TLS certificates for the configured domain. The app has no public published port; only the proxy is exposed. Cookies are Secure, HttpOnly and SameSite=Strict in production. Explicit host allowlisting and same-origin checks apply. Requests cannot choose a team different from the signed-in session.

The included Docker recipe runs without root, drops Linux capabilities, uses a read-only application filesystem and a durable `/data` volume. It is an unbuilt deployment recipe until tested on your actual Docker host. The dependency installer version is pinned; review and pin the approved base-image digests for your release process.

## Limits and behavior

- All Gemini calls in one process share a 12 requests/minute pacer (`AGENTFORGE_GEMINI_RPM`). Separate processes and apps do not share it; token and daily project quotas still apply.
- Two saved runs execute concurrently; eight total run slots include active and queued runs.
- Two conversations/image extractions execute concurrently. A team may have only one active request at a time.
- Twelve expensive endpoint requests per client/team per minute; eight login attempts per client per minute. The reverse proxy's IP may be shared because forwarded headers are deliberately not trusted by the app; tune this only after configuring a trusted proxy boundary.
- Live agents have bounded graph/tool calls, provider timeouts and limited retries. A missing required tool gets one correction turn; failure remains explicit.
- Reports are saved after every specialist. A restart marks unfinished runs interrupted. A retry is a new request and can incur new provider usage; there is no invisible simulation or automatic re-execution after restart.
- A failed run's completed specialist reports remain available for diagnosis; exports require successful completion.
- `/api/health` checks service availability and exposes no key. `/api/ready` checks storage, configuration and whether a live response has succeeded since this process started. Run an actual agent after a restart before readiness passes. This is an observed check, not a continuing guarantee of provider availability.
- Input/output token counts are recorded per agent report when provided by Gemini. They are not an invoice; check actual provider billing separately.

## Back up and restore

```sh
uv run agentforge-jarvis backup .agentforge/workshop-backup.sqlite3
```

This uses SQLite's online backup API. Keep backups private because they contain team data and credential hashes. For restoration, stop the app, preserve the existing data directory, restore the verified backup as `agentforge.sqlite3` in a clean data directory, set `AGENTFORGE_DATA_DIR` to that directory and restart. Test the restored notes/runs/team sign-in before relying on the backup.

## Before admitting a classroom

Verify the actual HTTPS URL, team sign-in and isolation, provider quota for concurrent teams, a full live swarm, memory citation, image extraction, export, restart recovery and backup restoration. Rehearse the expected number of pairs and measure queue time. A successful local test does not establish capacity for 65 or 200 simultaneous students. Use small staggered groups until the measured host/provider limits support more.

No remote server, TLS certificate, Docker image build or classroom-scale load result is claimed by this source package. Those require the selected host and real classroom concurrency.
