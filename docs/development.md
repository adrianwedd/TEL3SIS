# Developer Guide

This guide explains how to set up a TEL3SIS development environment, run pre-commit hooks, execute tests, and contribute changes.

## Environment Setup

1. **Clone & enter repo**
   ```bash
   git clone https://github.com/yourname/TEL3SIS.git
   cd TEL3SIS
   ```
2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   pre-commit install
   ```
   Installing the hooks ensures formatting and secret scanning run automatically.
3. **Create `.env`**
   ```bash
   cp .env.example .env
   # populate Twilio, OpenAI, ElevenLabs, Deepgram, EMBEDDING_PROVIDER, EMBEDDING_MODEL_NAME, etc.
   ```
4. **Local development and testing**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   pre-commit install
   pytest -q
   ```

## Running Pre-commit

`pre-commit` formats code with Black, lints with Ruff, and scans for secrets. Hooks run automatically when committing. Run them manually on changed files with:

```bash
pre-commit run --files <changed files>
```

To check the entire repository:

```bash
pre-commit run --all-files
```

## Testing

Run the `pytest` suite:

```bash
pytest -q
```

Unit tests live under `tests/`. End-to-end call emulation is available via `tel3sis dev-call`, and latency warmup via `tel3sis warmup`.

## Pull Request Workflow

1. Create a feature branch using `<phase>/<task_id>-short-desc`.
2. Ensure `pre-commit` and `pytest` pass locally.
3. Push your branch and open a PR referencing the task ID from `tasks.yml`.
4. Follow the PR template:

```
### Task
- ID: <task id>
### Description
Describe what the PR does.
### Checklist
- [ ] Tests added
- [ ] Docs updated
- [ ] CI green
```

CI must succeed and at least one reviewer must approve before merging.
