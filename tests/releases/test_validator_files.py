import errno
import stat
from unittest.mock import Mock, patch

import gfal2

from cernopendata.modules.releases.validations.files import ValidFiles


class DummyRelease:
    def __init__(self, records):
        self.records = records


def test_validate_missing_metadata():
    release = DummyRelease([{"files": [{"uri": "a"}, {"uri": "b", "checksum": "abc"}]}])

    validator = ValidFiles()
    errors = validator.validate(release)

    assert errors == [
        "Entry 1, file 1: Missing size",
        "Entry 1, file 1: Missing checksum",
        "Entry 1, file 2: Missing size",
        "Entry 1, file 2: Invalid checksum 'abc'",
    ]


def test_validate_valid_files():
    release = DummyRelease(
        [{"files": [{"uri": "a", "checksum": "adler32:abc", "size": 10}]}]
    )

    validator = ValidFiles()
    assert validator.validate(release) == []


def test_validate_invalid_checksum():
    release = DummyRelease([{"files": [{"uri": "a", "checksum": "abc", "size": 10}]}])

    validator = ValidFiles()

    assert validator.validate(release) == ["Entry 1, file 1: Invalid checksum 'abc'"]


def test_validate_no_files():
    release = DummyRelease([{}])
    validator = ValidFiles()

    assert validator.validate(release) == []


def test_get_entry_details():
    validator = ValidFiles()

    context = Mock()
    context.stat.return_value = Mock(
        st_mode=stat.S_IFREG, st_size=10
    )  # regular file, not a dir
    context.checksum.return_value = "abc"
    assert validator._get_entry_details(context, "root://a") == (
        False,
        10,
        "adler32:abc",
    )

    context.checksum.side_effect = gfal2.GError(
        "Checksum not found", errno.ENOENT
    )  # ENOENT: no such file or directory
    assert validator._get_entry_details(context, "root://a") == (False, 10, None)


@patch("cernopendata.modules.releases.validations.files.gfal2")
def test_fix_adds_and_repairs_checksums(gfal2_mock):
    release = DummyRelease(
        [
            {
                "files": [
                    {"uri": "root://missing"},
                    {"uri": "root://bare", "checksum": "abc", "size": 99},
                    {"uri": "root://valid", "checksum": "adler32:def", "size": 20},
                ]
            }
        ]
    )
    validator = ValidFiles()

    with patch.object(
        validator, "_get_entry_details", return_value=(False, 10, "adler32:xyz")
    ):
        errors = validator.fix(release)

    files = release.records[0]["files"]
    assert errors == []
    assert files[0] == {"uri": "root://missing", "checksum": "adler32:xyz", "size": 10}
    assert files[1] == {"uri": "root://bare", "checksum": "adler32:xyz", "size": 99}
    assert files[2] == {"uri": "root://valid", "checksum": "adler32:def", "size": 20}


@patch("cernopendata.modules.releases.validations.files.gfal2")
def test_fix_keeps_bare_checksum_when_uncomputable(gfal2_mock):
    release = DummyRelease([{"files": [{"uri": "root://a", "checksum": "abc"}]}])
    validator = ValidFiles()

    with patch.object(validator, "_get_entry_details", return_value=(False, 10, None)):
        errors = validator.fix(release)

    assert errors == []
    assert release.records[0]["files"][0] == {
        "uri": "root://a",
        "checksum": "abc",
        "size": 10,
    }
