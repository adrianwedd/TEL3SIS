"""CoordinatorAgent for TEL3SIS.

This agent reads ``tasks.yml`` to manage the swarm task board and
interacts with GitHub to apply labels or update status.  The initial
implementation only exposes a few helper methods.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import os

from github import Github
import yaml


@dataclass
class CoordinatorAgent:
    """Lightweight interface for project coordination."""

    token: Optional[str] = None
    repo_name: Optional[str] = None
    tasks_path: str = "tasks.yml"

    def __post_init__(self) -> None:
        self._github = Github(self.token or os.getenv("GITHUB_TOKEN"))
        self._repo = self._github.get_repo(
            self.repo_name or os.getenv("GITHUB_REPOSITORY", "")
        )

    # ------------------------------------------------------------------
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Return the list of tasks from ``tasks.yml``."""
        with open(self.tasks_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("tasks", [])

    # ------------------------------------------------------------------
    def label_pr(self, pr_number: int, labels: List[str]) -> None:
        """Add labels to a pull request."""
        pr = self._repo.get_pull(pr_number)
        pr.add_to_labels(*labels)

    # ------------------------------------------------------------------
    def update_status(
        self, task_id: int, status: str, message: str | None = None
    ) -> None:
        """Update the status of a task in ``tasks.yml`` and commit the change."""
        tasks = self.load_tasks()
        updated = False
        for task in tasks:
            if task.get("id") == task_id:
                task["status"] = status
                updated = True
                break

        if not updated:
            raise ValueError(f"Task {task_id} not found")

        new_content = yaml.safe_dump({"tasks": tasks}, sort_keys=False)
        file = self._repo.get_contents(self.tasks_path)
        commit_msg = message or f"chore(tasks): set {task_id} status to {status}"
        self._repo.update_file(file.path, commit_msg, new_content, file.sha)
