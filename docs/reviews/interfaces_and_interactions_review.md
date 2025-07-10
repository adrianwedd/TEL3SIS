# Part 2 – Interfaces & Interactions Review (Updated)

This section revisits how TEL3SIS exposes functionality to users and other systems. It focuses on REST APIs, command line usability, and key third‑party integrations.

## REST Endpoints
- **`/v1/oauth/start`** – begin Google OAuth flow.
- **`/v1/oauth/callback`** – handle OAuth callback and store credentials.
- **`/v1/inbound_call`** *(POST)* – main webhook used by Twilio to start a conversation.
- **`/v1/recording_status`** *(POST)* – Twilio callback when a recording is available.
- **`/v1/calls`** – JSON listing of past calls.
- **`/v1/dashboard`** – protected dashboard of calls.
- **`/v1/dashboard/<call_id>`** – detailed transcript/audio view.
- **`/v1/login` / `/v1/login` (POST)** – dashboard login form.
- **`/v1/login/oauth`** – OAuth based login.
- **`/v1/logout`** – end dashboard session.
- **`/v1/metrics`** – Prometheus metrics scraping.

## CLI Usability
- **`scripts/dev_test_call.py`** – talk to the agent using local audio devices.
- **`scripts/warmup_whisper.py`** – preload the Whisper model so first calls are faster.
- **`scripts/red_team.py`** – run adversarial prompts; writes YAML output with `-o`.
- **`scripts/manage.py`** – helper for DB migrations and user creation.

The scripts work but are scattered. A unified `tel3sis` CLI wrapping these commands would improve discoverability.

## External Integrations
- **Twilio** – voice calls and SMS notifications.
- **Google Calendar** – event creation via OAuth.
- **Weather API** – simple weather reports.
- **SendGrid** – email transcripts and alerts.
- **Prometheus & Grafana** – metrics and dashboards.
- **OpenAI/Whisper/ElevenLabs** – LLM, STT and TTS used through `vocode-python`.

Strengths include validated request data with Pydantic and graceful degradation when credentials are missing. Weaknesses include inconsistent error handling and lack of integration tests.

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
  status: done
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
