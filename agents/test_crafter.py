"""TestCrafterPro agent utilities."""

from __future__ import annotations

__test__ = False

from dataclasses import dataclass
from typing import Optional
from server.settings import Settings
import xml.etree.ElementTree as ET
from github import Github


@dataclass
class TestCrafterPro:
    """Simple helper to verify coverage and comment on pull requests."""

    token: Optional[str] = None
    repo_name: Optional[str] = None
    coverage_path: str = "coverage.xml"
    threshold: float = 80.0

    def __post_init__(self) -> None:
        cfg = Settings()
        self._github = Github(self.token or cfg.github_token)
        self._repo = self._github.get_repo(self.repo_name or cfg.github_repository)

    def read_coverage(self) -> float:
        """Return line coverage percentage from ``coverage.xml``."""
        tree = ET.parse(self.coverage_path)
        root = tree.getroot()
        rate = float(root.attrib.get("line-rate", 0)) * 100
        return rate

    def verify_and_comment(self, pr_number: int) -> bool:
        """If coverage meets the threshold, post an approval comment."""
        pct = self.read_coverage()
        if pct >= self.threshold:
            pr = self._repo.get_pull(pr_number)
            pr.create_issue_comment("/agent TC verify_coverage")
            return True
        return False
