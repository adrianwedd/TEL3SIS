# Contributing to TEL3SIS

Thank you for helping improve **TEL3SIS**! This guide covers how to set up the development environment, run the automated checks, and open pull requests.

## Environment Setup

1. **Clone the repository** and create a Python 3.11 virtual environment:
   ```bash
   git clone https://github.com/yourname/TEL3SIS.git
   cd TEL3SIS
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```
2. **Install `git-secrets`** to prevent committing credentials:
   ```bash
   sudo apt-get install -y git-secrets
   git secrets --install -f
   ```

## Pre-commit Hooks

Install the hooks and run them before every push:

```bash
pre-commit install
pre-commit run --all-files
```

The hooks format with **Black**, lint with **Ruff**, scan with **git-secrets**, and build the docs.

## Running Tests

Execute the test suite locally to catch regressions:

```bash
pytest -q
```

## Branch and PR Naming

Follow the workflow defined in `AGENTS.md`:

- Branches use `<phase>/<task_id>-slug`.
  Example:
  ```bash
  git checkout -b core-mvp/CORE-01-setup
  ```
- Commits follow the Conventional Commits style: `type(scope): summary`.
- Pull requests must reference the task ID and use the template:
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

Ensure `pre-commit` and `pytest` pass before opening a PR.

## Updating Dependencies

Runtime packages live in `requirements.in` and development tools in `requirements-dev.in`. After modifying these files, regenerate the lock files:

```bash
pip-compile requirements.in
pip-compile requirements-dev.in
```
Commit the updated `.txt` files with your change.

## Docker Image Security Scanning

All pull requests run a Trivy scan via `security.yml`. You can verify locally:

```bash
docker build -t tel3sis .
trivy image --severity HIGH --no-progress tel3sis
```
