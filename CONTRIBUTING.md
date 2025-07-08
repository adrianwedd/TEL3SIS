# Contributing to TEL3SIS

Thank you for helping improve **TEL3SIS**! Please follow the guidelines below to keep contributions consistent.

## Code Style

- Format Python code with [Black](https://black.readthedocs.io/).
- Lint using [Ruff](https://github.com/astral-sh/ruff).
- Write clear docstrings for modules and functions.
- Commit messages use the Conventional Commits `type(scope): summary` style.

## Setup

1. **Clone the repository**
2. **Install development tools**
   ```bash
   pip install -r requirements.txt
   pip install pre-commit
   sudo apt-get install -y git-secrets
   git secrets --install -f
   ```
3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```
   Hooks include `black`, `ruff`, and `git-secrets` which scans for tokens.
   To manually check the repository run:
   ```bash
   git secrets --scan -r
   ```

## Branch Naming

Create feature branches using `<phase>/<task_id>-short-desc`. Examples:

```bash
git checkout -b dev/INIT-00-scaffold
```

## Pre-commit Workflow

Run hooks locally before pushing:

```bash
pre-commit run --files <changed files>
```

Hooks will format with Black, lint with Ruff, and scan with git-secrets.

## Pull Request Process

1. Ensure `pre-commit` and `pytest` pass.
2. Push your branch and open a PR referencing the task ID from `tasks.yml`.
3. Follow the PR template:

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
4. CI must succeed and at least one reviewer must approve.

## Docker Image Security Scanning

All pull requests trigger a Trivy scan in `security.yml`. The workflow builds the `tel3sis` image and fails if any **HIGH** severity CVEs are detected.
You can run the scan locally:

```bash
docker build -t tel3sis .
trivy image --severity HIGH --no-progress tel3sis
```

