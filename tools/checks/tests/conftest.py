from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from support import (
    GIT_VARS,
    commit,
    git,
    git_out,
    init_repo,
    stage,
)


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in GIT_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return init_repo(tmp_path / "repo")


@pytest.fixture
def conflicted(repo: Path) -> Path:
    stage(repo, "c.wav", 10)
    stage(repo, "fixtures/synthetic/d.wav", 10)
    commit(repo, "base")
    git(repo, "checkout", "-q", "-b", "one")
    stage(repo, "c.wav", 20)
    stage(repo, "fixtures/synthetic/d.wav", 20)
    commit(repo, "one")
    git(repo, "checkout", "-q", "-b", "two", "HEAD~1")
    stage(repo, "c.wav", 30)
    stage(repo, "fixtures/synthetic/d.wav", 30)
    commit(repo, "two")
    merge = subprocess.run(["git", "merge", "-q", "one"], cwd=repo, capture_output=True)
    assert merge.returncode != 0
    assert len(git_out(repo, "ls-files", "-s", "--", "c.wav").splitlines()) == 3
    assert len(git_out(repo, "ls-files", "-s", "--", "fixtures/synthetic/d.wav").splitlines()) == 3
    return repo


@pytest.fixture
def plain_dir(tmp_path: Path) -> Path:
    root = tmp_path / "plain"
    root.mkdir()
    return root
