import gfal2
import pytest

from cernopendata.modules.releases.validations.expand_files import (
    CheckExpandDirectories,
    FileExpansionError,
)


class DummyRelease:
    def __init__(self, records):
        self.records = records


# -------------------------
# validate
# -------------------------
def test_validate_detects_wildcard():
    release = DummyRelease(records=[{"files": [{"uri": "root://some/path/*"}]}])

    validator = CheckExpandDirectories()
    errors = validator.validate(release)

    assert len(errors) == 1
    assert "root://some/path/*" in errors[0]


def test_validate_no_files_field():
    release = DummyRelease(records=[{}])

    validator = CheckExpandDirectories()
    errors = validator.validate(release)

    assert errors == []


def test_validate_no_wildcard():
    release = DummyRelease(records=[{"files": [{"uri": "root://some/path/file.root"}]}])

    validator = CheckExpandDirectories()
    errors = validator.validate(release)

    assert errors == []


# -------------------------
# _walk
# -------------------------
def test_walk_recursion(monkeypatch):
    validator = CheckExpandDirectories()

    class DummyCtx:
        def listdir(self, uri):
            if uri.endswith("base"):
                return ["dir1", "file1"]
            elif uri.endswith("dir1"):
                return ["file2"]
            return []

    def fake_get_entry_details(ctx, uri):
        if uri.endswith("dir1"):
            return True, None, None  # directory
        return False, 123, "abc"  # file

    monkeypatch.setattr(
        CheckExpandDirectories,
        "_get_entry_details",
        staticmethod(fake_get_entry_details),
    )

    results = list(validator._walk(DummyCtx(), "root://base"))

    assert len(results) == 2
    uris = [r["uri"] for r in results]

    assert "root://base/file1" in uris
    assert "root://base/dir1/file2" in uris


def test_fix_no_files_field():
    validator = CheckExpandDirectories()

    release = DummyRelease(records=[{}])

    errors = validator.fix(release)

    assert errors == []
