import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import NamedTuple

MEDIA_EXTENSIONS = frozenset(
    {
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
    }
)
MAX_SYNTHETIC_BYTES = 1048576
GITLINK_MODE = b"160000"


class Entry(NamedTuple):
    path: str
    size: int | None


class Violation(NamedTuple):
    path: str
    reason: str


class NotARepo(Exception):
    pass


def in_synthetic_dir(path: str) -> bool:
    directories = PurePosixPath(path).parts[:-1]
    return any(
        directories[i] == "fixtures" and directories[i + 1] == "synthetic"
        for i in range(len(directories) - 1)
    )


def is_media(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in MEDIA_EXTENSIONS


def check(entries: Iterable[Entry]) -> list[Violation]:
    violations: list[Violation] = []
    for path, size in entries:
        if not is_media(path):
            continue
        if not in_synthetic_dir(path):
            violations.append(Violation(path, "media file"))
        elif size is None:
            violations.append(Violation(path, "synthetic fixture size unknown"))
        elif size > MAX_SYNTHETIC_BYTES:
            violations.append(Violation(path, "synthetic fixture over 1 MiB"))
    return violations


def index_entries(repo: Path) -> list[Entry]:
    top = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
    )
    if top.returncode != 0:
        raise NotARepo(str(repo))
    root = os.fsdecode(top.stdout.rstrip(b"\n"))
    listing = subprocess.run(
        ["git", "-C", root, "ls-files", "-z", "-s"], check=True, capture_output=True
    )
    blobs: dict[str, bytes] = {}
    for record in listing.stdout.split(b"\0"):
        if not record:
            continue
        meta, _, raw_path = record.partition(b"\t")
        mode, sha, _stage = meta.split(b" ")
        if mode == GITLINK_MODE:
            continue
        blobs.setdefault(os.fsdecode(raw_path), sha)
    sizes: dict[str, int] = {}
    wanted = [path for path in blobs if is_media(path) and in_synthetic_dir(path)]
    if wanted:
        answer = subprocess.run(
            ["git", "-C", root, "cat-file", "--batch-check=%(objectsize)"],
            check=True,
            capture_output=True,
            input=b"".join(blobs[path] + b"\n" for path in wanted),
            env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        )
        for path, line in zip(wanted, answer.stdout.splitlines(), strict=True):
            if not line.endswith(b" missing"):
                sizes[path] = int(line)
    return [Entry(path, sizes.get(path)) for path in blobs]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        print("usage: no_media.py", file=sys.stderr)
        return 2
    try:
        cwd = Path.cwd()
    except FileNotFoundError:
        print("no_media: not a git repository", file=sys.stderr)
        return 2
    try:
        entries = index_entries(cwd)
    except NotARepo:
        print("no_media: not a git repository", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print("no_media: git not found", file=sys.stderr)
        return 2
    violations = check(entries)
    for violation in violations:
        shown = os.fsencode(violation.path).decode("utf-8", "backslashreplace")
        print(f"{shown}: {violation.reason}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
