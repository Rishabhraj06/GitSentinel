"""Conventional commit generator using git diff analysis and AI/heuristic synthesis."""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CommitGenerator:
    """Analyzes git diffs and generates standardized conventional commit messages."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = Path(repo_dir)

    def get_staged_diff(self) -> str:
        """Fetch staged git diff. Fallback to unstaged diff if nothing is staged."""
        try:
            # 1. Try staged diff
            out = subprocess.check_output(
                ["git", "-C", str(self.repo_dir), "diff", "--cached"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore")
            if out.strip():
                return out

            # 2. Try unstaged working tree diff
            out = subprocess.check_output(
                ["git", "-C", str(self.repo_dir), "diff", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore")
            return out
        except (subprocess.SubprocessError, FileNotFoundError):
            return ""

    def get_changed_files(self) -> List[Tuple[str, str]]:
        """Return list of (status, filename) from git status --porcelain."""
        try:
            out = subprocess.check_output(
                ["git", "-C", str(self.repo_dir), "status", "--porcelain"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore")
            changes = []
            for line in out.splitlines():
                if len(line) >= 4:
                    status = line[:2].strip()
                    fname = line[3:].strip()
                    changes.append((status, fname))
            return changes
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    def generate_message(self, context_hint: Optional[str] = None) -> Dict[str, str]:
        """Generate a conventional commit title and description."""
        diff = self.get_staged_diff()
        changes = self.get_changed_files()

        if not changes and not diff:
            return {
                "title": "chore: no active changes detected in repository",
                "body": "Working tree is clean. Stage or modify files before generating commit.",
                "type": "chore"
            }

        # Check if Gemini API is available for AI generation
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key and len(diff) > 20:
            try:
                ai_result = self._generate_with_gemini(diff, changes, context_hint, api_key)
                if ai_result:
                    return ai_result
            except Exception:
                pass  # Graceful fallback to heuristic engine

        # Heuristic Rule-Based Generation (Fast, offline, reliable)
        return self._generate_heuristic(changes, diff, context_hint)

    def _generate_heuristic(
        self,
        changes: List[Tuple[str, str]],
        diff: str,
        context_hint: Optional[str]
    ) -> Dict[str, str]:
        """Synthesize conventional commit message using heuristic file and diff analysis."""
        files = [fname for _, fname in changes]
        extensions = {Path(f).suffix for f in files}
        file_basenames = [Path(f).name.lower() for f in files]

        # Determine type
        commit_type = "chore"
        scope = "repo"

        # Check for tests
        if any("test" in f.lower() for f in files):
            commit_type = "test"
            scope = "suite"
        # Check for documentation
        elif all(ext in (".md", ".txt", ".rst") or "doc" in f.lower() for ext in extensions for f in files):
            commit_type = "docs"
            scope = "readme" if any("readme" in b for b in file_basenames) else "docs"
        # Check for build / dependencies
        elif any(b in ("package.json", "requirements.txt", "pyproject.toml", "setup.py", "dockerfile") for b in file_basenames):
            commit_type = "chore"
            scope = "deps"
        # Check for fix vs feat based on diff content
        elif "fix" in (context_hint or "").lower() or "bug" in (context_hint or "").lower():
            commit_type = "fix"
            scope = self._infer_scope(files)
        elif any(status in ("A", "??") for status, _ in changes):
            commit_type = "feat"
            scope = self._infer_scope(files)
        else:
            commit_type = "refactor" if "refactor" in (context_hint or "").lower() else "fix"
            scope = self._infer_scope(files)

        # Build Title
        if context_hint:
            subject = context_hint.strip().rstrip(".")
        else:
            primary_file = Path(files[0]).stem if files else "core"
            if commit_type == "feat":
                subject = f"implement initial {primary_file} functionality"
            elif commit_type == "fix":
                subject = f"resolve issues in {primary_file}"
            elif commit_type == "docs":
                subject = "update project documentation and guidelines"
            elif commit_type == "test":
                subject = "add unit tests and verification suite"
            else:
                subject = f"update {primary_file} and maintenance configuration"

        title = f"{commit_type}({scope}): {subject.lower()}"

        # Build Body
        body_lines = [f"- Modified {len(files)} file(s):"]
        for f in files[:5]:
            body_lines.append(f"  * {f}")
        if len(files) > 5:
            body_lines.append(f"  * ... and {len(files) - 5} more files")

        return {
            "title": title,
            "body": "\n".join(body_lines),
            "type": commit_type,
            "scope": scope
        }

    def _infer_scope(self, files: List[str]) -> str:
        """Infer module scope from affected file paths."""
        if not files:
            return "core"
        first = Path(files[0])
        parts = first.parts
        if len(parts) > 1 and parts[0] not in ("src", "lib"):
            return parts[0].lower()
        if len(parts) > 2 and parts[0] in ("src", "lib"):
            return parts[1].lower()
        return first.stem.lower()

    def _generate_with_gemini(
        self,
        diff: str,
        changes: List[Tuple[str, str]],
        context_hint: Optional[str],
        api_key: str
    ) -> Optional[Dict[str, str]]:
        """Call Gemini API to generate concise senior-level conventional commit message."""
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = (
                "You are an expert software engineer following Conventional Commits (type(scope): subject).\n"
                f"Context hint: {context_hint or 'None'}\n"
                f"Changed files: {[f for _, f in changes]}\n"
                f"Git diff snippet (truncated to 3000 chars):\n{diff[:3000]}\n\n"
                "Provide ONLY the commit title on the first line (e.g. 'feat(auth): add JWT validation middleware').\n"
                "Followed by an empty line, then 2-3 concise bullet points summarizing changes."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text.strip()
            lines = text.split("\n", 1)
            title = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            return {"title": title, "body": body, "type": "ai"}
        except Exception:
            return None
