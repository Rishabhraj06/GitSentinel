"""Unit tests for GitSentinel security & bloat scanner."""

import tempfile
from pathlib import Path
from gitsentinel.scanner import SecurityScanner


def test_detect_sensitive_env_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        env_file = tmp_path / ".env"
        env_file.write_text("DATABASE_URL=postgres://user:pass@localhost:5432/db")

        scanner = SecurityScanner(tmp_path)
        findings = scanner.scan_path()

        assert any(f.category == "SECRET" and ".env" in f.file_path for f in findings)


def test_detect_hardcoded_openai_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code_file = tmp_path / "app.py"
        code_file.write_text('API_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890"')

        scanner = SecurityScanner(tmp_path)
        findings = scanner.scan_path()

        secret_findings = [f for f in findings if f.category == "SECRET"]
        assert len(secret_findings) > 0
        assert "OpenAI API Secret Key" in secret_findings[0].message


def test_detect_eval_code_smell():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code_file = tmp_path / "unsafe.py"
        code_file.write_text('user_input = "2 + 2"\nresult = eval(user_input)\n')

        scanner = SecurityScanner(tmp_path)
        findings = scanner.scan_path()

        smell_findings = [f for f in findings if f.category == "SMELL"]
        assert len(smell_findings) > 0
        assert "eval" in smell_findings[0].message


def test_clean_directory_has_zero_findings():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code_file = tmp_path / "clean.py"
        code_file.write_text('def greet(name: str) -> str:\n    return f"Hello {name}"\n')

        scanner = SecurityScanner(tmp_path)
        findings = scanner.scan_path()

        assert len(findings) == 0
