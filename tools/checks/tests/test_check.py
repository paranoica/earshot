from __future__ import annotations

import os
from pathlib import Path

import pytest
from support import (
    EXTENSIONS,
    MEDIA,
    MIB,
    OVER,
    UNKNOWN,
    entry,
    violation,
    write,
)

import no_media


def test_entry_has_path_and_size_fields() -> None:
    item = no_media.Entry(path="a.wav", size=7)
    assert no_media.Entry._fields == ("path", "size")
    assert tuple(item) == ("a.wav", 7)


def test_violation_has_path_and_reason_fields() -> None:
    item = no_media.Violation(path="a.wav", reason=MEDIA)
    assert no_media.Violation._fields == ("path", "reason")
    assert tuple(item) == ("a.wav", MEDIA)


def test_check_on_empty_input_returns_no_violations() -> None:
    assert no_media.check([]) == []


@pytest.mark.parametrize("ext", EXTENSIONS)
def test_every_media_extension_fails(ext: str) -> None:
    assert no_media.check([entry(f"clip{ext}")]) == [violation(f"clip{ext}", MEDIA)]


@pytest.mark.parametrize("path", ["app.ts", "src/index.ts", "big.ts"])
def test_typescript_ts_extension_passes(path: str) -> None:
    assert no_media.check([entry(path, 5 * MIB)]) == []


@pytest.mark.parametrize("path", ["X.WAV", "song.Mp3", "deep/dir/CLIP.MOV", "a.OgG", "v.MPEG"])
def test_uppercase_media_extension_fails(path: str) -> None:
    assert no_media.check([entry(path)]) == [violation(path, MEDIA)]


def test_uppercase_extension_under_synthetic_obeys_size_limit() -> None:
    small = "fixtures/synthetic/A.WAV"
    big = "fixtures/synthetic/B.FLAC"
    assert no_media.check([entry(small, MIB), entry(big, MIB + 1)]) == [violation(big, OVER)]


@pytest.mark.parametrize(
    "path", ["notes.wav.md", "ogg.py", ".wav", "wav", "README.md", "clips.wav/notes.txt"]
)
def test_look_alike_names_pass(path: str) -> None:
    assert no_media.check([entry(path, MIB + 1)]) == []


@pytest.mark.parametrize(
    "path",
    [
        "fixtures/synthetic/a.wav",
        "server/tests/fixtures/synthetic/b.ogg",
        "fixtures/synthetic/deep/nested/c.mp3",
        "a/fixtures/synthetic/b/c/d.opus",
    ],
)
def test_small_media_under_synthetic_dir_at_any_depth_passes(path: str) -> None:
    assert no_media.check([entry(path, 1000)]) == []


@pytest.mark.parametrize(
    "path",
    [
        "fixtures/synthetic/a.wav",
        "server/tests/fixtures/synthetic/b.ogg",
        "fixtures/synthetic/deep/nested/c.mp3",
    ],
)
def test_big_media_under_synthetic_dir_at_any_depth_fails_as_over(path: str) -> None:
    assert no_media.check([entry(path, MIB + 1)]) == [violation(path, OVER)]


@pytest.mark.parametrize(
    "path",
    [
        "fixtures/synthetic-old/a.wav",
        "xfixtures/synthetic/a.wav",
        "fixtures/xsynthetic/a.wav",
        "fixtures-old/synthetic/a.wav",
        "Fixtures/Synthetic/a.wav",
        "Fixtures/synthetic/a.wav",
        "fixtures/Synthetic/a.wav",
        "fixtures/synthetic.wav",
        "fixtures/other/synthetic/a.wav",
        "synthetic/fixtures/a.wav",
        "fixtures/a.wav",
        "synthetic/a.wav",
        "fixtures_synthetic/a.wav",
        "fixtures.synthetic/a.wav",
    ],
)
def test_media_in_look_alike_synthetic_dir_fails_as_media(path: str) -> None:
    assert no_media.check([entry(path, 10)]) == [violation(path, MEDIA)]


def test_file_named_synthetic_is_not_a_synthetic_dir() -> None:
    path = "fixtures/synthetic"
    assert no_media.check([entry(path, 10)]) == []
    assert no_media.check([entry("fixtures/synthetic.ogg", 10)]) == [
        violation("fixtures/synthetic.ogg", MEDIA)
    ]


@pytest.mark.parametrize(
    ("size", "expected"),
    [(0, []), (1, []), (MIB - 1, []), (MIB, []), (MIB + 1, [OVER]), (10 * MIB, [OVER])],
)
def test_synthetic_size_boundary_is_one_mib(size: int, expected: list[str]) -> None:
    path = "fixtures/synthetic/tone.wav"
    assert no_media.check([entry(path, size)]) == [violation(path, r) for r in expected]


@pytest.mark.parametrize("size", [0, 1, MIB, MIB + 1])
def test_media_outside_synthetic_fails_at_any_size(size: int) -> None:
    assert no_media.check([entry("call.ogg", size)]) == [violation("call.ogg", MEDIA)]


@pytest.mark.parametrize(
    "path", ["data.bin", "model.onnx", "fixtures/synthetic/big.json", "fixtures/synthetic/x.txt"]
)
def test_big_non_media_passes(path: str) -> None:
    assert no_media.check([entry(path, 10**10)]) == []


def test_violations_keep_input_order() -> None:
    entries = [
        entry("z.wav"),
        entry("README.md", 10 * MIB),
        entry("fixtures/synthetic/big.ogg", MIB + 1),
        entry("a.mp3"),
        entry("fixtures/synthetic/small.ogg", 10),
        entry("m.mkv"),
    ]
    assert no_media.check(entries) == [
        violation("z.wav", MEDIA),
        violation("fixtures/synthetic/big.ogg", OVER),
        violation("a.mp3", MEDIA),
        violation("m.mkv", MEDIA),
    ]


def test_check_accepts_one_shot_iterator() -> None:
    entries = iter([entry("first.wav"), entry("ok.txt"), entry("last.mov")])
    assert no_media.check(entries) == [violation("first.wav", MEDIA), violation("last.mov", MEDIA)]


def test_check_returns_paths_verbatim() -> None:
    paths = ["записи/звонок 1.mp3", "line\nbreak.wav", os.fsdecode(b"notes\xff.wav")]
    assert no_media.check([entry(p) for p in paths]) == [violation(p, MEDIA) for p in paths]


def test_check_uses_entry_size_not_disk(plain_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write(plain_dir, "fixtures/synthetic/disk_big.wav", 2 * MIB)
    write(plain_dir, "fixtures/synthetic/disk_small.wav", 1)
    monkeypatch.chdir(plain_dir)
    entries = [
        entry("fixtures/synthetic/disk_big.wav", 10),
        entry("fixtures/synthetic/disk_small.wav", 2 * MIB),
    ]
    assert no_media.check(entries) == [violation("fixtures/synthetic/disk_small.wav", OVER)]


@pytest.mark.parametrize(
    "path",
    [
        "fixtures/synthetic/a.wav",
        "server/tests/fixtures/synthetic/b.ogg",
        "a/fixtures/synthetic/b/c/d.opus",
        "fixtures/synthetic/LOUD.WAV",
    ],
)
def test_synthetic_media_with_unknown_size_fails_closed(path: str) -> None:
    assert no_media.check([entry(path, None)]) == [violation(path, UNKNOWN)]


@pytest.mark.parametrize(
    "path",
    ["call.ogg", "fixtures/synthetic-old/a.wav", "fixtures/a.wav", "Fixtures/Synthetic/a.wav"],
)
def test_media_outside_synthetic_with_unknown_size_is_media_file(path: str) -> None:
    assert no_media.check([entry(path, None)]) == [violation(path, MEDIA)]


@pytest.mark.parametrize(
    "path",
    ["README.md", "fixtures/synthetic/x.txt", "fixtures/synthetic", "notes.wav.md", "app.ts"],
)
def test_non_media_with_unknown_size_passes(path: str) -> None:
    assert no_media.check([entry(path, None)]) == []


def test_unknown_size_violations_keep_input_order() -> None:
    entries = [
        entry("fixtures/synthetic/first.wav", None),
        entry("fixtures/synthetic/ok.wav", 0),
        entry("notes.txt", None),
        entry("mid.mp3", None),
        entry("fixtures/synthetic/big.wav", MIB + 1),
        entry("fixtures/synthetic/last.ogg", None),
    ]
    assert no_media.check(entries) == [
        violation("fixtures/synthetic/first.wav", UNKNOWN),
        violation("mid.mp3", MEDIA),
        violation("fixtures/synthetic/big.wav", OVER),
        violation("fixtures/synthetic/last.ogg", UNKNOWN),
    ]
