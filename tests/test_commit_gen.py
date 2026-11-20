"""Unit tests for GitSentinel conventional commit generator."""

import tempfile
from pathlib import Path
from gitsentinel.commit_gen import CommitGenerator


def test_heuristic_commit_generation_for_features():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        gen = CommitGenerator(tmp_path)

        changes = [("??", "src/auth/login.py"), ("??", "src/auth/token.py")]
        res = gen._generate_heuristic(changes, diff="", context_hint="add OAuth login")

        assert res["type"] == "feat"
        assert "feat(" in res["title"]
        assert "oauth login" in res["title"].lower()


def test_heuristic_commit_generation_for_docs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        gen = CommitGenerator(tmp_path)

        changes = [("M", "README.md"), ("M", "docs/architecture.md")]
        res = gen._generate_heuristic(changes, diff="", context_hint="")

        assert res["type"] == "docs"
        assert "docs(" in res["title"]


def test_heuristic_commit_generation_for_tests():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        gen = CommitGenerator(tmp_path)

        changes = [("A", "tests/test_api.py")]
        res = gen._generate_heuristic(changes, diff="", context_hint="test suite")

        assert res["type"] == "test"
