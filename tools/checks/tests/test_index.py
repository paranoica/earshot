from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from support import (
    MEDIA,
    MIB,
    UNKNOWN,
    add_cacheinfo,
    commit,
    entry,
    git,
    git_out,
    init_repo,
    missing_objects,
    stage,
    write,
)

import no_media


def test_index_entries_looks_up_size_only_for_synthetic_media(repo: Path) -> None:
    stage(repo, "a.txt", 1234)
    stage(repo, "b/c.wav", 0)
    stage(repo, "big.mp3", 2 * MIB)
    stage(repo, "fixtures/synthetic/d.wav", 1234)
    stage(repo, "fixtures/synthetic/empty.wav", 0)
    stage(repo, "fixtures/synthetic/G.WAV", 3)
    stage(repo, "fixtures/synthetic/e.txt", 50)
    stage(repo, "fixtures/synthetic-old/f.wav", 7)
    assert sorted(no_media.index_entries(repo)) == [
        entry("a.txt", None),
        entry("b/c.wav", None),
        entry("big.mp3", None),
        entry("fixtures/synthetic-old/f.wav", None),
        entry("fixtures/synthetic/G.WAV", 3),
        entry("fixtures/synthetic/d.wav", 1234),
        entry("fixtures/synthetic/e.txt", None),
        entry("fixtures/synthetic/empty.wav", 0),
    ]


def test_index_entries_returns_entry_instances(repo: Path) -> None:
    stage(repo, "a.txt", 3)
    result = no_media.index_entries(repo)
    assert isinstance(result, list)
    assert all(isinstance(item, no_media.Entry) for item in result)


def test_index_entries_on_empty_index_returns_empty_list(repo: Path) -> None:
    assert no_media.index_entries(repo) == []


def test_index_entries_lists_staged_then_deleted_file_with_staged_size(repo: Path) -> None:
    stage(repo, "call.ogg", 5000).unlink()
    stage(repo, "fixtures/synthetic/call.ogg", 5000).unlink()
    assert sorted(no_media.index_entries(repo)) == [
        entry("call.ogg", None),
        entry("fixtures/synthetic/call.ogg", 5000),
    ]


def test_index_entries_reports_staged_size_after_truncation_on_disk(repo: Path) -> None:
    stage(repo, "fixtures/synthetic/call.wav", 3 * MIB).write_bytes(b"")
    assert no_media.index_entries(repo) == [entry("fixtures/synthetic/call.wav", 3 * MIB)]


def test_index_entries_reports_staged_size_after_growth_on_disk(repo: Path) -> None:
    stage(repo, "fixtures/synthetic/tone.wav", 5).write_bytes(b"\0" * 500)
    stage(repo, "notes.txt", 5).write_bytes(b"\0" * 500)
    assert sorted(no_media.index_entries(repo)) == [
        entry("fixtures/synthetic/tone.wav", 5),
        entry("notes.txt", None),
    ]


def test_index_entries_skips_untracked_file(repo: Path) -> None:
    stage(repo, "a.txt", 4)
    write(repo, "untracked.wav", 100)
    write(repo, "dir/untracked.ogg", 100)
    write(repo, "fixtures/synthetic/untracked.wav", 100)
    assert no_media.index_entries(repo) == [entry("a.txt", None)]


def test_index_entries_from_subdirectory_lists_whole_repo(repo: Path) -> None:
    stage(repo, "root.txt", 11)
    stage(repo, "sub/dir/inner.wav", 22)
    stage(repo, "other/x.mp3", 33)
    stage(repo, "other/fixtures/synthetic/t.wav", 44)
    assert sorted(no_media.index_entries(repo / "sub" / "dir")) == [
        entry("other/fixtures/synthetic/t.wav", 44),
        entry("other/x.mp3", None),
        entry("root.txt", None),
        entry("sub/dir/inner.wav", None),
    ]


def test_index_entries_decodes_non_utf8_name_without_crash(repo: Path) -> None:
    name = os.fsdecode(b"notes\xff.wav")
    synthetic = os.fsdecode(b"fixtures/synthetic/tone\xff.wav")
    stage(repo, name, 7)
    stage(repo, synthetic, 8)
    assert (repo / name).exists()
    assert os.fsencode(repo / name).endswith(b"notes\xff.wav")
    assert sorted(no_media.index_entries(repo)) == [entry(synthetic, 8), entry(name, None)]


def test_index_entries_returns_name_with_newline_exactly(repo: Path) -> None:
    stage(repo, "line\nbreak.wav", 9)
    stage(repo, "fixtures/synthetic/line\nbreak.wav", 10)
    assert sorted(no_media.index_entries(repo)) == [
        entry("fixtures/synthetic/line\nbreak.wav", 10),
        entry("line\nbreak.wav", None),
    ]


def test_index_entries_returns_spaces_and_non_ascii_exactly(repo: Path) -> None:
    stage(repo, "записи/звонок 1.mp3", 12)
    stage(repo, 'tab\tquote".ogg', 13)
    stage(repo, "fixtures/synthetic/звонок 2.mp3", 14)
    assert sorted(no_media.index_entries(repo)) == [
        entry("fixtures/synthetic/звонок 2.mp3", 14),
        entry('tab\tquote".ogg', None),
        entry("записи/звонок 1.mp3", None),
    ]


@pytest.mark.parametrize("path", ["x.txt", "fixtures/synthetic/x.txt"])
def test_non_media_with_missing_blob_is_listed_without_size(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], path: str
) -> None:
    add_cacheinfo(repo, "100644", path)
    assert no_media.index_entries(repo) == [entry(path, None)]
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (0, "", "")


@pytest.mark.parametrize("path", ["x.wav", "fixtures/synthetic-old/x.wav"])
def test_media_outside_synthetic_with_missing_blob_is_media_file(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], path: str
) -> None:
    add_cacheinfo(repo, "100644", path)
    assert no_media.index_entries(repo) == [entry(path, None)]
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, f"{path}: {MEDIA}\n", "")


@pytest.mark.parametrize("path", ["fixtures/synthetic/m.wav", "a/fixtures/synthetic/b/M.OGG"])
def test_synthetic_media_with_missing_blob_fails_as_size_unknown(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], path: str
) -> None:
    add_cacheinfo(repo, "100644", path)
    assert no_media.index_entries(repo) == [entry(path, None)]
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, f"{path}: {UNKNOWN}\n", "")


@pytest.mark.parametrize("path", ["sub.wav", "fixtures/synthetic/sub.wav"])
def test_gitlink_is_skipped(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], path: str
) -> None:
    add_cacheinfo(repo, "160000", path)
    stage(repo, "a.txt", 3)
    assert no_media.index_entries(repo) == [entry("a.txt", None)]
    monkeypatch.chdir(repo)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (0, "", "")


def test_index_entries_lists_conflicted_path_once(conflicted: Path) -> None:
    result = no_media.index_entries(conflicted)
    assert sorted(item.path for item in result) == ["c.wav", "fixtures/synthetic/d.wav"]
    sizes = dict(result)
    assert sizes["c.wav"] is None
    assert sizes["fixtures/synthetic/d.wav"] in {10, 20, 30}


def test_main_prints_conflicted_path_once(
    conflicted: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(conflicted)
    code = no_media.main([])
    out, err = capsys.readouterr()
    assert (code, out, err) == (1, f"c.wav: {MEDIA}\n", "")


@pytest.fixture
def partial_clone(tmp_path: Path) -> tuple[Path, Path]:
    src = init_repo(tmp_path / "src")
    stage(src, "rec.wav", 2 * MIB)
    stage(src, "fixtures/synthetic/s.wav", 100)
    stage(src, "notes.txt", 50)
    commit(src, "init")
    bare = tmp_path / "bare.git"
    git(tmp_path, "clone", "-q", "--bare", str(src), str(bare))
    git(bare, "config", "uploadpack.allowFilter", "true")
    cloned = subprocess.run(
        [
            "git",
            "-c",
            "uploadpack.allowFilter=true",
            "clone",
            "-q",
            "--filter=blob:none",
            "--no-checkout",
            bare.as_uri(),
            "clone",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    version = git_out(tmp_path, "--version").strip()
    reason = cloned.stderr.lower()
    unsupported = "filter" in reason and ("not recognized" in reason or "not supported" in reason)
    if cloned.returncode != 0 and unsupported:
        pytest.skip(f"{version} cannot make a blob:none partial clone: {cloned.stderr.strip()}")
    assert cloned.returncode == 0, cloned.stderr
    clone = tmp_path / "clone"
    git(clone, "read-tree", "HEAD")
    if not missing_objects(clone):
        pytest.skip(f"{version} fetched every blob despite --filter=blob:none")
    return clone, bare


@pytest.mark.parametrize("remote", ["kept", "removed"])
def test_partial_clone_lookup_does_not_download_blobs(
    partial_clone: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    remote: str,
) -> None:
    clone, bare = partial_clone
    if remote == "removed":
        shutil.rmtree(bare)
    before = missing_objects(clone)
    blobs = {
        git_out(clone, "rev-parse", f":{p}").strip()
        for p in ("rec.wav", "notes.txt", "fixtures/synthetic/s.wav")
    }
    assert blobs <= before
    sizes = dict(no_media.index_entries(clone))
    assert before <= missing_objects(clone)
    assert sizes == {"rec.wav": None, "notes.txt": None, "fixtures/synthetic/s.wav": None}
    capfd.readouterr()
    monkeypatch.chdir(clone)
    code = no_media.main([])
    out, err = capfd.readouterr()
    assert before <= missing_objects(clone)
    assert code == 1
    assert sorted(out.splitlines()) == [
        f"fixtures/synthetic/s.wav: {UNKNOWN}",
        f"rec.wav: {MEDIA}",
    ]
    assert err == ""


def test_not_a_repo_is_an_exception() -> None:
    assert issubclass(no_media.NotARepo, Exception)


def test_index_entries_outside_repo_raises_not_a_repo(plain_dir: Path) -> None:
    with pytest.raises(no_media.NotARepo):
        no_media.index_entries(plain_dir)
