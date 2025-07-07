"""SafetyOracle agent utilities."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional

from github import Github


@dataclass
class SafetyOracle:
    """Simple helper to scan PR diffs for unsafe patterns."""

    token: Optional[str] = None
    repo_name: Optional[str] = None
    banned_patterns: Optional[List[str]] = None

    def __post_init__(self) -> None:
        self._github = Github(self.token or os.getenv("GITHUB_TOKEN"))
        self._repo = self._github.get_repo(
            self.repo_name or os.getenv("GITHUB_REPOSITORY", "")
        )
        if self.banned_patterns is None:
            self.banned_patterns = [
                r"openai\.api_key",
                r"api_key\s*=",
                r"password\s*=",
                r"secret(?:_key|_token)?\s*=",
            ]

    # ------------------------------------------------------------------
    def _fetch_diff(self, pr_number: int) -> str:
        """Return the unified diff for a pull request."""
        pr = self._repo.get_pull(pr_number)
        patches: List[str] = []
        for file in pr.get_files():
            if file.patch:
                patches.append(file.patch)
        return "\n".join(patches)

    # ------------------------------------------------------------------
    def _is_safe(self, diff: str) -> bool:
        """Check diff against banned patterns."""
        for pattern in self.banned_patterns or []:
            if re.search(pattern, diff, re.IGNORECASE):
                return False
        return True

    # ------------------------------------------------------------------
    def review_pr(self, pr_number: int) -> bool:
        """Post approval comment if PR diff passes safety checks."""
        diff = self._fetch_diff(pr_number)
        if self._is_safe(diff):
            pr = self._repo.get_pull(pr_number)
            pr.create_issue_comment("/agent SO risk_ack")
            return True
        return False
