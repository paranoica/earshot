from __future__ import annotations

import secrets
import subprocess
from pathlib import Path

import no_media

MIB = 1048576
MEDIA = "media file"
OVER = "synthetic fixture over 1 MiB"
UNKNOWN = "synthetic fixture size unknown"
EXTENSIONS = [
    ".ogg",
    ".oga",
    ".opus",
    ".wav",
    ".mp3",
    ".m4a",
    ".m4b",
    ".aac",
    ".flac",
    ".amr",
    ".3gp",
    ".wma",
    ".aiff",
    ".aif",
    ".caf",
    ".webm",
    ".mp4",
    ".m4v",
    ".mkv",
    ".mov",
    ".avi",
    ".wmv",
    ".flv",
    ".mpeg",
    ".mpg",
]
GIT_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_NO_LAZY_FETCH",
    "GIT_CONFIG_PARAMETERS",
)


def entry(path: str, size: int | None = 10) -> no_media.Entry:
    return no_media.Entry(path=path, size=size)


def violation(path: str, reason: str) -> no_media.Violation:
    return no_media.Violation(path=path, reason=reason)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def git_out(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return done.stdout


def absent_oid(repo: Path) -> str:
    form = git_out(repo, "rev-parse", "--show-object-format").strip()
    return secrets.token_hex(32 if form == "sha256" else 20)


def add_cacheinfo(repo: Path, mode: str, rel: str) -> None:
    git(repo, "update-index", "--add", "--cacheinfo", f"{mode},{absent_oid(repo)},{rel}")


def missing_objects(repo: Path) -> set[str]:
    out = git_out(repo, "rev-list", "--objects", "--missing=print", "--all")
    return {line[1:] for line in out.splitlines() if line.startswith("?")}


def commit(repo: Path, message: str) -> None:
    git(repo, "commit", "-q", "--no-verify", "-m", message)


def write(repo: Path, rel: str, size: int) -> Path:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"\0" * size)
    return target


def stage(repo: Path, rel: str, size: int) -> Path:
    target = write(repo, rel, size)
    git(repo, "add", "--", rel)
    return target


def init_repo(root: Path) -> Path:
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.invalid")
    return root
