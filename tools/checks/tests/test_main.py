from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from support import (
    MEDIA,
    MIB,
    OVER,
    stage,
    write,
)

import no_media


def test_main_prints_exact_violation_lines_and_returns_1(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, "a.wav", 10)
    stage(repo, "README.md", 2 * MIB)
    stage(repo, "fixtures/synthetic/big.ogg", MIB + 1)
    stage(repo, "fixtures/synthetic/ok.ogg", MIB)
    stage(repo, "записи/звонок 1.mp3", 3)
    write(repo, "untracked.wav", 10)
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert code == 1
    assert out.endswith("\n")
    assert sorted(out.splitlines()) == [
        "a.wav: media file",
        "fixtures/synthetic/big.ogg: synthetic fixture over 1 MiB",
        "записи/звонок 1.mp3: media file",
    ]
    assert err == ""


def test_main_from_subdirectory_checks_whole_repo(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, "top.wav", 10)
    stage(repo, "sub/notes.txt", 10)
    monkeypatch.chdir(repo / "sub")
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, "top.wav: media file\n", "")


def test_main_on_clean_repo_returns_0_and_prints_nothing(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, "README.md", 10)
    stage(repo, "data.bin", 3 * MIB)
    stage(repo, "fixtures/synthetic/tone.wav", MIB)
    write(repo, "untracked.wav", 10)
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (0, "", "")


def test_main_on_empty_repo_returns_0(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (0, "", "")


def test_main_reports_staged_then_deleted_recording(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, "call.ogg", 100).unlink()
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, "call.ogg: media file\n", "")


def test_main_reports_staged_then_truncated_synthetic_fixture(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, "fixtures/synthetic/big.wav", 3 * MIB).write_bytes(b"")
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, f"fixtures/synthetic/big.wav: {OVER}\n", "")


def test_main_prints_non_utf8_media_name_with_backslash_escape(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, os.fsdecode(b"notes\xff.wav"), 7)
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, "notes\\xff.wav: media file\n", "")


@pytest.mark.parametrize("argv", [["."], ["a.wav"], ["a.wav", "b.wav"], ["--all"], ["--help"]])
def test_main_with_any_argument_prints_usage_and_returns_2(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    stage(repo, "a.wav", 10)
    monkeypatch.chdir(repo)
    code = no_media.main(argv)
    out, err = capsys.readouterr()
    assert code == 2
    assert out == ""
    assert len(err.splitlines()) == 1
    assert "usage" in err.lower()
    assert "Traceback" not in err


def test_main_outside_repo_prints_exact_error_and_returns_2(
    plain_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write(plain_dir, "call.wav", 10)
    monkeypatch.chdir(plain_dir)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert code == 2
    assert out == ""
    assert err == "no_media: not a git repository\n"
    assert "Traceback" not in err


def test_main_without_git_executable_prints_exact_error_and_returns_2(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stage(repo, "a.wav", 10)
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PATH", str(empty))
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (2, "", "no_media: git not found\n")


@pytest.mark.parametrize("parent", ["tmp", "repo"])
def test_main_in_deleted_cwd_prints_not_a_repo_and_returns_2(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    parent: str,
) -> None:
    stage(repo, "a.wav", 10)
    gone = (tmp_path if parent == "tmp" else repo) / "gone"
    gone.mkdir()
    monkeypatch.chdir(gone)
    gone.rmdir()
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (2, "", "no_media: not a git repository\n")


def test_main_without_argv_reads_sys_argv_and_rejects_argument(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage(repo, "a.wav", 10)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["no_media.py", "x"])
    code = no_media.main()
    out, err = capsys.readouterr()
    assert code == 2
    assert out == ""
    assert len(err.splitlines()) == 1
    assert "usage" in err.lower()
    assert "Traceback" not in err


@pytest.mark.parametrize(
    ("rel", "expected"), [("README.md", (0, "", "")), ("a.wav", (1, f"a.wav: {MEDIA}\n", ""))]
)
def test_main_without_argv_and_no_arguments_checks_repo(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    rel: str,
    expected: tuple[int, str, str],
) -> None:
    stage(repo, rel, 10)
    write(repo, "untracked.wav", 10)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["no_media.py"])
    code = no_media.main()
    out, err = capsys.readouterr()
    assert (code, out, err) == expected
