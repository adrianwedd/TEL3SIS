"""SafetyOracle agent utilities."""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
import hashlib
from datetime import datetime, timedelta

from github import Github
from server.settings import Settings
from logging_config import logger


@dataclass
class SafetyOracle:
    """Advanced security scanner for PR diffs with pattern matching and violation reporting."""

    token: Optional[str] = None
    repo_name: Optional[str] = None
    banned_patterns: Optional[List[str]] = None
    
    # Configuration for analysis depth
    enable_advanced_patterns: bool = True
    cache_results: bool = True
    report_detailed_violations: bool = True

    def __post_init__(self) -> None:
        cfg = Settings()
        self._github = Github(self.token or cfg.github_token)
        self._repo = self._github.get_repo(self.repo_name or cfg.github_repository)
        if self.banned_patterns is None:
            self.banned_patterns = self._get_advanced_security_patterns()
        
        # Cache for expensive operations
        self._pattern_cache: Dict[str, bool] = {}
        self._file_hash_cache: Dict[str, str] = {}
        self._last_cache_clear = datetime.now()
    
    def _get_advanced_security_patterns(self) -> List[str]:
        """Return comprehensive security patterns for code review."""
        return [
            # API Keys and Secrets
            r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][^'\"]{10,}['\"]?",
            r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]?",
            r"(?i)(?:private[_-]?key|rsa[_-]?key)\s*[:=]",
            r"(?i)bearer\s+[a-zA-Z0-9_-]{20,}",
            
            # Hardcoded credentials
            r"(?i)(?:mysql|postgres|mongodb)://[^\s]+:[^\s]+@",
            r"(?i)(?:admin|root|user)\s*[:=]\s*['\"](?:admin|password|123456|root)['\"]?",
            
            # Dangerous code patterns
            r"(?i)eval\s*\(",
            r"(?i)exec\s*\(",
            r"(?i)os\.system\s*\(",
            r"(?i)subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True",
            r"(?i)pickle\.loads?\s*\(",
            
            # SQL injection risks
            r"(?i)(?:SELECT|INSERT|UPDATE|DELETE).*%s",
            r"(?i)cursor\.execute\s*\([^)]*%",
            
            # XSS and injection risks
            r"(?i)innerHTML\s*=.*\+",
            r"(?i)document\.write\s*\(.*\+",
            
            # File system risks
            r"(?i)open\s*\([^)]*\.\./",
            r"(?i)os\.path\.join\s*\([^)]*\.\./",
            
            # Network security
            r"(?i)verify\s*=\s*False",
            r"(?i)ssl[._]create_default_context\s*\([^)]*check_hostname\s*=\s*False",
            
            # Debug/test code in production
            r"(?i)debug\s*=\s*True",
            r"(?i)print\s*\([^)]*(?:password|secret|token|key)",
            r"(?i)console\.log\s*\([^)]*(?:password|secret|token|key)",
        ]

    def _fetch_diff(self, pr_number: int) -> str:
        """Return the unified diff for a pull request with file filtering."""
        pr = self._repo.get_pull(pr_number)
        patches: List[str] = []
        
        # Only analyze relevant file types
        relevant_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".cpp", ".c", ".cs", ".php", ".rb", ".rs", ".sql", ".sh", ".yml", ".yaml", ".json", ".env"}
        
        for file in pr.get_files():
            if file.patch and any(file.filename.endswith(ext) for ext in relevant_extensions):
                patches.append(f"--- File: {file.filename} ---\n{file.patch}")
        
        return "\n".join(patches)

    def _is_safe(self, diff: str) -> bool:
        """Check diff against banned patterns with caching and detailed analysis."""
        # Create cache key from diff content
        diff_hash = hashlib.sha256(diff.encode()).hexdigest()
        
        # Check cache first
        if diff_hash in self._pattern_cache:
            return self._pattern_cache[diff_hash]
        
        # Clear cache if too old (prevent memory bloat)
        if datetime.now() - self._last_cache_clear > timedelta(hours=1):
            self._pattern_cache.clear()
            self._file_hash_cache.clear()
            self._last_cache_clear = datetime.now()
        
        violations = self._detect_security_violations(diff)
        is_safe = len(violations) == 0
        
        # Cache result
        self._pattern_cache[diff_hash] = is_safe
        
        if not is_safe:
            logger.bind(violations=violations).warning("security_violations_detected")
        
        return is_safe
    
    def _detect_security_violations(self, diff: str) -> List[Dict[str, str]]:
        """Detect and categorize security violations in diff."""
        violations = []
        
        for pattern in self.banned_patterns or []:
            matches = list(re.finditer(pattern, diff, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                # Get line context
                lines = diff[:match.start()].count('\n')
                line_content = diff.split('\n')[lines] if lines < len(diff.split('\n')) else ""
                
                violations.append({
                    "pattern": pattern,
                    "match": match.group(0),
                    "line": lines + 1,
                    "context": line_content.strip(),
                    "severity": self._get_violation_severity(pattern)
                })
        
        return violations
    
    def _get_violation_severity(self, pattern: str) -> str:
        """Determine severity level of security violation."""
        high_severity_keywords = ["api_key", "secret", "password", "private_key", "token"]
        medium_severity_keywords = ["eval", "exec", "system", "shell=True"]
        
        pattern_lower = pattern.lower()
        
        if any(keyword in pattern_lower for keyword in high_severity_keywords):
            return "HIGH"
        elif any(keyword in pattern_lower for keyword in medium_severity_keywords):
            return "MEDIUM"
        else:
            return "LOW"

    def review_pr(self, pr_number: int) -> bool:
        """Post approval comment if PR diff passes safety checks."""
        try:
            diff = self._fetch_diff(pr_number)
            violations = self._detect_security_violations(diff)
            
            pr = self._repo.get_pull(pr_number)
            
            if len(violations) == 0:
                pr.create_issue_comment("/agent SO risk_ack - No security violations detected")
                logger.bind(pr_number=pr_number).info("pr_safety_approved")
                return True
            else:
                # Create detailed violation report
                violation_report = self._create_violation_report(violations)
                pr.create_issue_comment(f"/agent SO risk_flag - Security violations detected:\n\n{violation_report}")
                logger.bind(pr_number=pr_number, violations_count=len(violations)).warning("pr_safety_rejected")
                return False
                
        except Exception as exc:
            logger.bind(pr_number=pr_number, error=str(exc)).error("pr_review_failed")
            return False
    
    def _create_violation_report(self, violations: List[Dict[str, str]]) -> str:
        """Create formatted report of security violations."""
        if not violations:
            return "No violations found."
        
        report_lines = ["## Security Violations Detected\n"]
        
        # Group by severity
        by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for violation in violations:
            by_severity[violation["severity"]].append(violation)
        
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            if by_severity[severity]:
                report_lines.append(f"### {severity} Severity ({len(by_severity[severity])} issues)\n")
                for violation in by_severity[severity]:
                    report_lines.append(
                        f"- **Line {violation['line']}**: {violation['match']}\n"
                        f"  - Context: `{violation['context']}`\n"
                        f"  - Pattern: `{violation['pattern'][:50]}...`\n"
                    )
        
        report_lines.append("\n**Action Required**: Please review and remediate these security issues before merging.")
        return "\n".join(report_lines)
