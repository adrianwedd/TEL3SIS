# Part 4 – Build, Test & Deployment Review

This follow-up review examines how TEL3SIS packages and releases the application. It looks at the continuous integration workflows, identifies remaining testing gaps, and documents how deployment artifacts are produced.

## CI/CD Workflows
- **`ci.yml`** runs lint, tests and builds a Docker image for every push and pull request.
- **`security.yml`** scans the repository for secrets and vulnerabilities using TruffleHog and Trivy.
- **`ca_runner.yml`** keeps `tasks.yml` in sync by running the CoordinatorAgent on a schedule.
- There is **no workflow that publishes Docker images or release archives** when a version tag is created. Build artifacts are discarded after each run.

## Testing Gaps
- Unit and functional tests cover API routes, tasks and tool integrations. An end‑to‑end call flow test exists.
- The Docker Compose stack is not exercised in CI. There are no health checks verifying that containers start correctly.
- Coverage reports are generated locally but not uploaded or preserved for later inspection.

## Deployment Artifacts
- Docker images are built during CI but never pushed to a registry.
- Developers must build images locally to deploy; there are no versioned releases or tagged images.

## Proposed Tasks
```yaml
- id: 72
  task_id: CI-05
  epic: "Phase 6: UI + Ops"
  title: "Publish Docker image on release"
  description: "Create release workflow that builds and pushes tagged images to GHCR and attaches release notes."
  component: ci
  area: CI/CD
  dependencies: [38, 70]
  priority: 3
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Add .github/workflows/release.yml triggered on push tags."
    - "Build Docker image and push to ghcr.io/tel3sis."
    - "Create GitHub release with notes and link to the image."
  acceptance_criteria:
    - "Tagging a release uploads the container image and creates a release page."

- id: 73
  task_id: QA-04
  epic: "Phase 6: UI + Ops"
  title: "Test Docker Compose deployment"
  description: "Ensure the composed services start correctly using a CI job."
  component: testing
  area: Quality
  dependencies: [38]
  priority: 2
  status: pending
  assigned_to: null
  command: null
  actionable_steps:
    - "Spin up docker-compose in GitHub Actions."
    - "Run health checks against the web and worker services."
  acceptance_criteria:
    - "CI job passes with all containers healthy."
```
