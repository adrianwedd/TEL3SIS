# Part 3 – Build, Test & Deploy Review

This section reviews the project’s CI pipelines, dependency management approach, and Docker build processes.

## CI Workflows
- **`ci.yml`** runs three jobs:
  - **lint** – installs `ruff` and lints the repository.
  - **test** – installs requirements, runs `pre-commit` hooks, then `pytest`.
  - **build** – builds a Docker image using the project `Dockerfile`.
- **`security.yml`** scans pull requests using `trufflehog` for secrets and
  builds the Docker image to scan with **Trivy**.
- **`ca_runner.yml`** is scheduled to run `CoordinatorAgent` with a GitHub App
  token to keep task statuses in sync.

The workflows cover the basics but lack caching, resulting in slow builds on
every run.

## Dependency Management
The repository maintains a single `requirements.txt` with pinned versions. It
contains both production and development packages. Pre-commit installs formatting
tools separately during CI. There is no tool to generate locked requirements or
split dependencies by environment.

## Docker Build Processes
The `Dockerfile` uses `python:3.11-slim`, installs build dependencies, then
copies the entire repository. Docker Compose builds multiple services using this
same image. The CI workflow invokes a simple `docker build` with no caching or
multi-stage optimization. There is also no `.dockerignore`, so the build context
includes tests and documentation.

## Strengths
- CI enforces linting, tests, and security scanning on pull requests.
- The Dockerfile starts from a minimal base image.

## Weaknesses / Opportunities
- No caching of pip packages or Docker layers in GitHub Actions.
- Development and production dependencies are mixed together.
- Docker build context is large and the resulting image could be slimmer.

## Proposed Tasks
```yaml
- id: 69
  task_id: DEV-02
  epic: "Phase 3: Stability"
  title: "Adopt pip-tools for dependency management"
  description: "Use pip-tools to maintain locked runtime and dev requirements."
  component: tooling
  area: DevOps
  dependencies: [49]
  priority: 2
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Add requirements.in and requirements-dev.in."
    - "Run pip-compile to generate requirements.txt and requirements-dev.txt."
    - "Update CI and Dockerfile to install compiled requirements."
  acceptance_criteria:
    - "Pip-compile produces up-to-date locked files."
    - "CI installs from compiled requirements and passes."

- id: 70
  task_id: OPS-06
  epic: "Phase 4: Performance"
  title: "Optimize Docker build with multi-stage and .dockerignore"
  description: "Reduce image size and build context using multi-stage builds and .dockerignore."
  component: infrastructure
  area: CI/CD
  dependencies: []
  priority: 3
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Create .dockerignore to exclude tests and docs from the build context."
    - "Refactor Dockerfile to use a builder stage and slim runtime stage."
    - "Update docker-compose and CI workflows to use the new Dockerfile."
  acceptance_criteria:
    - "Docker image size decreases and build succeeds."
    - "CI build passes with the multi-stage Dockerfile."

- id: 71
  task_id: CI-04
  epic: "Phase 4: Performance"
  title: "Cache pip and Docker layers in CI"
  description: "Use GitHub Actions caches to speed up lint/test jobs and Docker builds."
  component: ci
  area: CI/CD
  dependencies: [38]
  priority: 3
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Configure actions/cache in ci.yml for pip wheels and Docker layers."
    - "Verify caching works across workflow runs."
  acceptance_criteria:
    - "CI completes faster on subsequent runs with cache hits."
```
