from unittest.mock import Mock, patch

import pytest

from cernopendata.modules.releases.validations.files import ValidFiles


class DummyRelease:
    def __init__(self, records):
        self.records = records


def test_validate_missing_metadata():
    release = DummyRelease([{"files": [{"uri": "a"}, {"uri": "b", "checksum": "abc"}]}])

    validator = ValidFiles()
    errors = validator.validate(release)

    assert errors == [
        "Entry 1, file 1: Missing size/checksum",
        "Entry 1, file 2: Missing size/checksum",
    ]


def test_validate_valid_files():
    release = DummyRelease([{"files": [{"uri": "a", "checksum": "abc", "size": 10}]}])

    validator = ValidFiles()
    assert validator.validate(release) == []


def test_validate_no_files():
    release = DummyRelease([{}])
    validator = ValidFiles()

    assert validator.validate(release) == []
