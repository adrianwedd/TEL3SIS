# AGENTS.md – Operating Manual for the TEL3SIS Swarm

> **Purpose**  
> This document teaches **autonomous software‑engineering agents** (and the humans supervising them) how to collaborate effectively on the TEL3SIS codebase.  
> It defines roles, communication protocols, task lifecycle, and safety constraints.

---

## 1 🔖 Agent Roles

| Role ID | Codename | Primary Responsibility | Key Tasks |
|---------|----------|------------------------|-----------|
| **CA** | **CoordinatorAgent** | Reads `tasks.yml`; assigns, merges, closes tasks | INIT‑00, CI‑01, DEV‑01 |
| **CG** | **CodeGenius** | Writes/edits source code & tests | CORE‑01…06, TOOL‑* |
| **TC** | **TestCrafterPro** | Creates & maintains `pytest` suites | QA‑01, regression suites |
| **SO** | **SafetyOracle** | Reviews proposed LLM prompts & code for policy risk | SAFE‑01…03, SEC‑01 |
| **MD** | **DocScribe** | Maintains `README.md`, `CONTRIBUTING.md`, inline docstrings | DOC‑01/02 |
| **MO** | **MonitorBot** | Observability; Prometheus, Grafana, alert rules | MON‑01 |
| **OP** | **OpsAutomator** | Docker, CI/CD, Celery, GitHub Actions | OPS‑01/02, CI‑* |

Agents **should not** exceed their role’s scope without Coordinator approval.

---

## 2 📜 Task Lifecycle

1. **Selection** – CoordinatorAgent reads `tasks.yml` (YAML list of dicts).  
2. **Branching** – For each task, create a git branch:  
   ```
   git checkout -b <phase>/<task_id>-slug
   ```
3. **Implementation** – CodeGenius / role agent modifies files.  
4. **Self‑Review** – Agent runs `pytest`, `ruff`, `black`, `pre‑commit`.  
5. **Pull Request** – Agent opens PR referencing `task_id`.  
6. **Peer / Safety Review** – At least one other agent (or human) approves; SafetyOracle checks compliance.  
7. **Merge & Close** – Coordinator merges, updates `tasks.yml` status → `done`.

> Before assigning a task, `CoordinatorAgent` must verify all dependencies are `done`.  
> If not, task status is set to `blocked` with reason `incomplete_dependency`.

### Multi‑Agent Review Sequence

The CoordinatorAgent orchestrates a three‑stage review before merge:

1. **Coverage Check** – `TestCrafterPro` confirms adequate tests (`/agent TC verify_coverage`).
2. **Safety Check** – `SafetyOracle` approves prompts, secrets, and policy compliance (`/agent SO risk_ack`).
3. **Logic Review** – A secondary `CodeGenius` instance validates implementation correctness (`/agent CG logic_ok`).

The PR may merge only after all three confirmations are present.

### Status keys in `tasks.yml`

- `pending` → `in_progress` → `in_review` → `done` or `blocked`.

**Agents must keep `tasks.yml` statuses up to date.**
When committing, update the relevant task entry (e.g. mark it `done`). The `CoordinatorAgent` will consolidate statuses after merge to prevent race conditions.

---

## 3 💬 Commit & PR Conventions

* **Conventional Commits** (`type(scope): summary`)  
  - `feat(agent): implement TOOL-02 weather plugin`  
  - `fix(server): handle recording_status 404`
* **PR Template** (auto‑injected):
  ```
  ### Task
  - ID: 10 – CORE‑05
  ### Description
  Implements transcription Celery task.
  ### Checklist
  - [x] Tests added
  - [x] Docs updated
  - [x] CI green
  ```

---

## 4 🛰 Communication Protocol

Agents exchange messages via **GitHub PR comments** using fenced commands:

```text
/agent <RoleID>
<free‑form rationale>
```

**Extended request example**

```text
/agent OP
type: request_change
file: docker-compose.yml
reason: |
  TOOL‑07 requires a new `geocoding` service.
  Please propose image and env configuration.
```

CoordinatorAgent parses these to route discussion.

---

## 5 🛡 Safety & Governance Rules

1. **No secrets in code** – All secrets must load from `.env`.
2. **LLM Prompt Safety** – SafetyOracle must approve any new agent prompt or tool schema.
3. **CI Required** – PRs merge only if `ci.yml` and `security.yml` succeed.
4. **Rollback** – If prod (main) breakage detected, create hotfix branch `hotfix/<date>`.

---

## 6 🗃 File Map Quick‑Ref

| Path | Owner Role | Purpose |
|------|------------|---------|
| `server/*.py` | CG | FastAPI + telephony |
| `agents/*.py` | CG, SO | Agent configs & filters |
| `tools/*.py` | CG | External integrations |
| `state/*.py` | CG | Redis/DB wrappers |
| `tests/` | TC | Pytest suites |
| `.github/workflows/` | OP | CI/CD pipelines |
| `ops/grafana/` | MO | Dashboards |

---

## 7 🔄 Automated Checks

| Tool | Hook | Blocking? |
|------|------|-----------|
| `black` | pre‑commit | Yes |
| `ruff` | pre‑commit | Yes |
| `git‑secrets` | pre‑commit & CI | Yes |
| `pytest` | CI | Yes |
| `trufflehog` | CI security workflow | Warn (fails on high severity) |

---

## 8 📅 Release Cadence

* **`main`** branch = deploy‑ready.  
* Minor releases tagged weekly `v0.Y.W` (Y‑year, W‑week).  
* Major milestones (Phase completions) tagged `v1.0`, `v2.0`, etc.

---

## 9 🤝 Escalation

If an agent is **blocked** > 24h, it must:

```
/agent CA
BLOCKED: waiting on input from <role>
```

Coordinator escalates to human maintainer **@AdrianW**.

---

*Updated: 2025‑07‑07*  

_“Build systematically, communicate explicitly, ship safely.”_
