# Part 2 – Interfaces & Interactions Review

This review summarizes how users and external systems interact with TEL3SIS. It covers HTTP API endpoints, command line utilities, and third‑party services.

## API Endpoints
- **`/v1/oauth/start`** – initiate Google OAuth flow for calendar access.
- **`/v1/oauth/callback`** – receive OAuth callback and store credentials.
- **`/v1/inbound_call`** (POST) – entry point for Twilio to start a conversation.
- **`/v1/recording_status`** (POST) – Twilio callback when a recording is available.
- **`/v1/calls`** – return JSON list of call records.
- **`/v1/dashboard`** – authenticated dashboard listing calls.
- **`/v1/dashboard/<call_id>`** – detailed view with transcript and audio.
- **`/v1/login/oauth`** – start OAuth login flow.
- **`/v1/metrics`** – Prometheus metrics endpoint.

## CLI Tools
- **`scripts/dev_test_call.py`** – local microphone/speaker conversation loop.
- **`scripts/warmup_whisper.py`** – preload the Whisper model so later calls are faster.
- **`scripts/red_team.py`** – run adversarial prompts against the agent; `-o` writes a YAML report.

## External Integrations
- **Twilio** – phone calls and SMS notifications.
- **Google Calendar** – OAuth workflow and event creation.
- **Weather API** – fetch simple weather reports via HTTP.
- **SendGrid** – send email transcripts and alerts.
- **Prometheus & Grafana** – metrics scraping and dashboards.
- **OpenAI/Whisper/ElevenLabs** – LLM, STT and TTS via `vocode-python`.

## Strengths
- Clear separation of routes using FastAPI routers.
- Pydantic models validate request data for most endpoints.
- CLI scripts help with development (local calls, red‑team testing).
- Integrations degrade gracefully when credentials are missing.

## Weaknesses / Opportunities
- No single reference for all endpoints; duplication exists for OAuth callbacks.
- CLI utilities are scattered rather than exposed as one cohesive tool.
- Error handling for external APIs is inconsistent.
- Lacking automated integration tests for the CLI or API.

## Proposed Tasks
```yaml
- id: 66
  task_id: DOC-06
  epic: "Phase 6: UI + Ops"
  title: "Publish API and CLI reference"
  description: "Add developer documentation listing all REST endpoints and command line tools."
  component: documentation
  area: DX
  dependencies: []
  priority: 2
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Generate a Markdown or OpenAPI spec summarizing available endpoints."
    - "Document usage examples for each CLI script."
  acceptance_criteria:
    - "README or docs folder contains a clear reference of APIs and CLI commands."

- id: 67
  task_id: CLI-01
  epic: "Phase 6: UI + Ops"
  title: "Provide unified `tel3sis` CLI"
  description: "Bundle existing helper scripts under a single Click-based entry point."
  component: tools
  area: DX
  dependencies: []
  priority: 3
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Create `tel3sis` CLI with subcommands for `serve`, `red-team`, `warmup`, and `dev-call`."
    - "Update documentation to reference the new CLI."
  acceptance_criteria:
    - "Running `tel3sis --help` lists available subcommands."
    - "Existing scripts continue to work via the CLI."

- id: 68
  task_id: QA-03
  epic: "Phase 6: UI + Ops"
  title: "Add integration tests for CLI and endpoints"
  description: "Exercise key CLI commands and API routes in pytest using mocked external services."
  component: testing
  area: Quality
  dependencies: []
  priority: 3
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Use `pytest` to invoke CLI subcommands and assert expected behavior."
    - "Mock Twilio and third-party APIs to verify endpoint flows."
  acceptance_criteria:
    - "All new tests pass and cover the CLI and API surfaces."
```
