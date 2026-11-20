"""Security & repository bloat scanner for GitSentinel."""

import os
import re
import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Secret detection patterns (Regex -> Description)
SECRET_PATTERNS = [
    (r"AIzaSy[0-9A-Za-z\-_]{33}", "Google Gemini / API Key"),
    (r"sk-[a-zA-Z0-9T3BlbkFJ]{20,}", "OpenAI API Secret Key"),
    (r"sk-ant-[a-zA-Z0-9_\-]{30,}", "Anthropic Claude API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token (Legacy)"),
    (r"github_pat_[0-9a-zA-Z_]{82}", "GitHub Fine-Grained Token"),
    (r"sk_live_[0-9a-zA-Z]{24}", "Stripe Live Secret Key"),
    (r"xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Bot / User Token"),
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Private Cryptographic Key"),
    (r"(?:api_key|secret_key|client_secret|auth_token)\s*=\s*['\"][0-9a-zA-Z\-_]{16,}['\"]", "Hardcoded Secret Assignment"),
]

# Sensitive filenames that should never be committed
SENSITIVE_FILENAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ecdsa", "id_ed25519",
    "credentials.json", "service-account.json", "client_secrets.json"
}

# Directories that indicate repository bloat if tracked
BLOAT_DIRECTORIES = {
    "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".next", "dist", "build"
}

# Max file size threshold (default: 5 MB)
DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024

@dataclass
class Finding:
    category: str  # "SECRET", "BLOAT", "SMELL"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    file_path: str
    line_number: Optional[int]
    message: str
    snippet: Optional[str] = None


class SecurityScanner:
    """Scans working directory or git files for security risks and repo bloat."""

    def __init__(self, root_dir: Path, max_file_size: int = DEFAULT_MAX_FILE_SIZE):
        self.root_dir = Path(root_dir)
        self.max_file_size = max_file_size

    def scan_path(self, target_path: Optional[Path] = None) -> List[Finding]:
        """Recursively scan a directory or file and return all findings."""
        base = Path(target_path) if target_path else self.root_dir
        findings: List[Finding] = []

        if base.is_file():
            findings.extend(self._scan_single_file(base))
            return findings

        for root, dirs, files in os.walk(base):
            # Skip .git directory
            if ".git" in dirs:
                dirs.remove(".git")

            # Check for bloat directories
            for d in list(dirs):
                if d in BLOAT_DIRECTORIES:
                    rel_dir = os.path.relpath(os.path.join(root, d), self.root_dir)
                    findings.append(Finding(
                        category="BLOAT",
                        severity="HIGH",
                        file_path=rel_dir,
                        line_number=None,
                        message=f"Untracked/staged bloat directory detected: '{d}'. Ensure it is in .gitignore."
                    ))

            for fname in files:
                fpath = Path(root) / fname
                rel_path = os.path.relpath(fpath, self.root_dir)

                # 1. Sensitive filename check
                if fname in SENSITIVE_FILENAMES or (fname.startswith(".env") and not fname.endswith(".example")):
                    findings.append(Finding(
                        category="SECRET",
                        severity="CRITICAL",
                        file_path=rel_path,
                        line_number=None,
                        message=f"Dangerous sensitive file detected: '{fname}'. Must be added to .gitignore."
                    ))

                # 2. Oversized file check
                try:
                    size = fpath.stat().st_size
                    if size > self.max_file_size:
                        mb = size / (1024 * 1024)
                        findings.append(Finding(
                            category="BLOAT",
                            severity="HIGH",
                            file_path=rel_path,
                            line_number=None,
                            message=f"File exceeds size threshold: {mb:.2f} MB (limit: {self.max_file_size / (1024*1024):.0f} MB)."
                        ))
                except OSError:
                    continue

                # 3. File content check (skip binary and huge files)
                if not self._is_binary(fpath) and fpath.stat().st_size < self.max_file_size:
                    findings.extend(self._scan_single_file(fpath))

        return findings

    def _scan_single_file(self, file_path: Path) -> List[Finding]:
        """Scan a text file for secret patterns and code smells."""
        findings = []
        rel_path = os.path.relpath(file_path, self.root_dir)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError:
            return findings

        content = "".join(lines)

        # A. Secret pattern scanner
        for lineno, line in enumerate(lines, start=1):
            line_str = line.strip()
            # Ignore comments in examples
            if line_str.startswith("#") and "example" in line_str.lower():
                continue

            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, line_str, re.IGNORECASE):
                    findings.append(Finding(
                        category="SECRET",
                        severity="CRITICAL",
                        file_path=rel_path,
                        line_number=lineno,
                        message=f"Potential leak detected: {desc}",
                        snippet=self._mask_secret(line_str)
                    ))

        # B. Python Code Smell / AST checks
        if file_path.suffix == ".py":
            findings.extend(self._check_python_ast(content, rel_path))

        return findings

    def _check_python_ast(self, content: str, rel_path: str) -> List[Finding]:
        """Parse Python AST to find dangerous anti-patterns like eval() or bare except."""
        findings = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            # Check dangerous eval/exec
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    findings.append(Finding(
                        category="SMELL",
                        severity="HIGH",
                        file_path=rel_path,
                        line_number=node.lineno,
                        message=f"Dangerous dynamic code execution call: '{node.func.id}()'",
                        snippet=f"{node.func.id}(...)"
                    ))

            # Check bare except: pass
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    findings.append(Finding(
                        category="SMELL",
                        severity="MEDIUM",
                        file_path=rel_path,
                        line_number=node.lineno,
                        message="Silent error suppression detected: 'except: pass'. Errors should be handled or logged.",
                        snippet="except: pass"
                    ))

        return findings

    @staticmethod
    def _is_binary(file_path: Path) -> bool:
        """Heuristic check for binary files."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\x00" in chunk
        except OSError:
            return False

    @staticmethod
    def _mask_secret(line: str) -> str:
        """Mask potential secrets in snippet output for safe display."""
        if len(line) > 80:
            line = line[:77] + "..."
        # Replace middle of suspected tokens with stars
        return re.sub(r"([a-zA-Z0-9_\-]{4})[a-zA-Z0-9_\-]{8,}([a-zA-Z0-9_\-]{4})", r"\1****\2", line)
