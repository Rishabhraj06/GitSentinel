"""Repository health and hygiene auditor for GitSentinel."""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

RECOMMENDED_GITIGNORE_ENTRIES = [
    ".env", "*.log", "__pycache__", ".DS_Store"
]

@dataclass
class HealthCheckResult:
    check_name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str
    recommendation: str


class RepoDoctor:
    """Diagnoses repository setup, git hygiene, and common anti-patterns."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = Path(repo_dir)

    def diagnose(self) -> Dict[str, Any]:
        """Run all diagnostic checks and compute a health score."""
        results: List[HealthCheckResult] = []

        results.append(self._check_git_repo())
        results.append(self._check_gitignore())
        results.append(self._check_readme_and_license())
        results.append(self._check_large_tracked_files())
        results.append(self._check_remote_sync())

        # Calculate Score
        passes = sum(1 for r in results if r.status == "PASS")
        warns = sum(1 for r in results if r.status == "WARN")
        fails = sum(1 for r in results if r.status == "FAIL")

        total = len(results)
        score = int(((passes * 1.0) + (warns * 0.5)) / total * 100)

        return {
            "score": score,
            "checks": results,
            "summary": f"{passes} passed, {warns} warnings, {fails} failed"
        }

    def _check_git_repo(self) -> HealthCheckResult:
        git_dir = self.repo_dir / ".git"
        if not git_dir.exists():
            return HealthCheckResult(
                check_name="Git Initialization",
                status="FAIL",
                message="Directory is not a Git repository.",
                recommendation="Run 'git init' to initialize version control."
            )
        return HealthCheckResult(
            check_name="Git Initialization",
            status="PASS",
            message="Git repository initialized properly.",
            recommendation="None."
        )

    def _check_gitignore(self) -> HealthCheckResult:
        gi_file = self.repo_dir / ".gitignore"
        if not gi_file.exists():
            return HealthCheckResult(
                check_name=".gitignore Hygiene",
                status="FAIL",
                message="No .gitignore file found in repository root.",
                recommendation="Create a .gitignore file to prevent accidental secret and build artifact commits."
            )

        content = gi_file.read_text(encoding="utf-8", errors="ignore")
        missing = [entry for entry in RECOMMENDED_GITIGNORE_ENTRIES if entry not in content]

        if missing:
            return HealthCheckResult(
                check_name=".gitignore Hygiene",
                status="WARN",
                message=f".gitignore exists but is missing common rules: {', '.join(missing)}",
                recommendation=f"Add missing patterns ({', '.join(missing)}) to .gitignore."
            )

        return HealthCheckResult(
            check_name=".gitignore Hygiene",
            status="PASS",
            message=".gitignore is present and covers essential patterns.",
            recommendation="None."
        )

    def _check_readme_and_license(self) -> HealthCheckResult:
        has_readme = any((self.repo_dir / f).exists() for f in ["README.md", "README.rst", "README.txt", "readme.md"])
        has_license = any((self.repo_dir / f).exists() for f in ["LICENSE", "LICENSE.md", "LICENSE.txt", "license"])

        if not has_readme:
            return HealthCheckResult(
                check_name="Documentation & License",
                status="WARN",
                message="Missing README.md file.",
                recommendation="Add a clear README.md to help users and recruiters understand the project."
            )
        if not has_license:
            return HealthCheckResult(
                check_name="Documentation & License",
                status="WARN",
                message="Missing LICENSE file.",
                recommendation="Add an open-source license (e.g. MIT, Apache 2.0) to clarify reuse rights."
            )
        return HealthCheckResult(
            check_name="Documentation & License",
            status="PASS",
            message="README and LICENSE are both present.",
            recommendation="None."
        )

    def _check_large_tracked_files(self) -> HealthCheckResult:
        try:
            out = subprocess.check_output(
                ["git", "-C", str(self.repo_dir), "ls-files"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore")
            large_files = []
            for rel in out.splitlines():
                fpath = self.repo_dir / rel
                if fpath.is_file() and fpath.stat().st_size > 10 * 1024 * 1024:
                    mb = fpath.stat().st_size / (1024 * 1024)
                    large_files.append(f"{rel} ({mb:.1f} MB)")

            if large_files:
                return HealthCheckResult(
                    check_name="Tracked Blob Sizes",
                    status="WARN",
                    message=f"Detected large files tracked in Git: {', '.join(large_files[:3])}",
                    recommendation="Remove large binaries from tracking and consider Git LFS."
                )
            return HealthCheckResult(
                check_name="Tracked Blob Sizes",
                status="PASS",
                message="No excessively large blobs (>10 MB) found in tracked files.",
                recommendation="None."
            )
        except Exception:
            return HealthCheckResult(
                check_name="Tracked Blob Sizes",
                status="PASS",
                message="Skipped (not a git working copy).",
                recommendation="None."
            )

    def _check_remote_sync(self) -> HealthCheckResult:
        try:
            remotes = subprocess.check_output(
                ["git", "-C", str(self.repo_dir), "remote", "-v"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore").strip()
            if not remotes:
                return HealthCheckResult(
                    check_name="Remote Origin",
                    status="WARN",
                    message="No remote origin configured.",
                    recommendation="Add a remote with 'git remote add origin <URL>' to backup and share code."
                )
            return HealthCheckResult(
                check_name="Remote Origin",
                status="PASS",
                message="Remote origin is configured properly.",
                recommendation="None."
            )
        except Exception:
            return HealthCheckResult(
                check_name="Remote Origin",
                status="WARN",
                message="Could not check git remotes.",
                recommendation="Ensure git is configured."
            )
