# Contributing to TEL3SIS

Thank you for helping improve **TEL3SIS**! This project follows the [Conventional Commits](https://www.conventionalcommits.org) standard and requires several pre-commit checks.

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

## Workflow

- Use branches named `<phase>/<task_id>-short-desc`.
- Run `pre-commit` before pushing.
- Open a pull request referencing the task ID in `tasks.yml`.
- CI must pass and at least one review is required.

