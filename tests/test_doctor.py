"""Unit tests for GitSentinel repository doctor."""

import tempfile
from pathlib import Path
from gitsentinel.doctor import RepoDoctor


def test_doctor_detects_missing_git_and_gitignore():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        doctor = RepoDoctor(tmp_path)
        diag = doctor.diagnose()

        assert diag["score"] < 100
        statuses = {c.check_name: c.status for c in diag["checks"]}
        assert statuses["Git Initialization"] == "FAIL"
        assert statuses[".gitignore Hygiene"] == "FAIL"


def test_doctor_passes_when_standards_met():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text(".env\n*.log\n__pycache__\n.DS_Store\n")
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "LICENSE").write_text("MIT License")

        doctor = RepoDoctor(tmp_path)
        diag = doctor.diagnose()

        statuses = {c.check_name: c.status for c in diag["checks"]}
        assert statuses["Git Initialization"] == "PASS"
        assert statuses[".gitignore Hygiene"] == "PASS"
        assert statuses["Documentation & License"] == "PASS"
        assert diag["score"] >= 80
