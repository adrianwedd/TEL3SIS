"""Secondary CodeGenius logic reviewer."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from server.config import Config

from github import Github


class LocalLLM:
    """Tiny offline LLM placeholder."""

    def __init__(self, model_name: str = "distilgpt2") -> None:
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        """Return a stub solution for the given prompt."""
        return "pass\n"


@dataclass
class CodeReviewer:
    """Helper to compare PR code with locally generated stub."""

    token: Optional[str] = None
    repo_name: Optional[str] = None
    threshold: float = 0.85
    llm: Optional[LocalLLM] = None

    def __post_init__(self) -> None:
        cfg = Config()
        self._github = Github(self.token or cfg.github_token)
        self._repo = self._github.get_repo(self.repo_name or cfg.github_repository)
        if self.llm is None:
            self.llm = LocalLLM()

    # ------------------------------------------------------------------
    def _fetch_diff(self, pr_number: int) -> str:
        """Return unified diff for a pull request."""
        pr = self._repo.get_pull(pr_number)
        patches: list[str] = []
        for file in pr.get_files():
            if file.patch:
                patches.append(file.patch)
        return "\n".join(patches)

    # ------------------------------------------------------------------
    def _semantic_similarity(self, a: str, b: str) -> float:
        """Return similarity ratio between two strings."""
        return SequenceMatcher(None, a, b).ratio()

    # ------------------------------------------------------------------
    def review_pr(self, pr_number: int, prompt: str) -> bool:
        """Comment approval if PR matches stub solution."""
        diff = self._fetch_diff(pr_number)
        stub = self.llm.generate(prompt)
        score = self._semantic_similarity(diff, stub)
        if score >= self.threshold:
            pr = self._repo.get_pull(pr_number)
            pr.create_issue_comment("/agent CG logic_ok")
            return True
        return False
