from unittest.mock import MagicMock, patch

from cernopendata.modules.releases.models import ReleaseStatus
from cernopendata.modules.releases.validations.duplicate_files import (
    CheckDuplicateFiles,
)


class DummyRelease:
    def __init__(self, records=None, status="DRAFT"):
        self.records = records or []
        self.status = ReleaseStatus[status].value if status else None


def test_validate_no_records_returns_no_errors():
    validator = CheckDuplicateFiles()
    release = DummyRelease(records=[])
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        errors = validator.validate(release)
    mock_fi.query.filter.assert_not_called()
    assert errors == []


def test_validate_records_with_no_files_returns_no_errors():
    validator = CheckDuplicateFiles()
    release = DummyRelease(records=[{"title": "no files key"}])
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        errors = validator.validate(release)
    mock_fi.query.filter.assert_not_called()
    assert errors == []


def test_validate_records_with_no_uris_returns_no_errors():
    validator = CheckDuplicateFiles()
    release = DummyRelease(records=[{"files": [{"checksum": "abc", "size": 10}]}])
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        errors = validator.validate(release)
    mock_fi.query.filter.assert_not_called()
    assert errors == []


def test_validate_no_collision_returns_no_errors():
    validator = CheckDuplicateFiles()
    release = DummyRelease(
        records=[{"files": [{"uri": "root://eos.cern.ch/file1.root"}]}]
    )
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        mock_fi.query.filter.return_value.all.return_value = []
        errors = validator.validate(release)
    assert errors == []


def test_validate_reports_colliding_uri():
    validator = CheckDuplicateFiles()
    uri = "root://eos.cern.ch/file1.root"
    release = DummyRelease(records=[{"files": [{"uri": uri}]}])
    fake_file = MagicMock(uri=uri)
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        mock_fi.query.filter.return_value.all.return_value = [fake_file]
        errors = validator.validate(release)
    assert len(errors) == 1
    assert uri in errors[0]
    assert "already stored" in errors[0]


def test_validate_reports_multiple_colliding_uris_in_one_error():
    validator = CheckDuplicateFiles()
    uri_a = "root://eos.cern.ch/a.root"
    uri_b = "root://eos.cern.ch/b.root"
    release = DummyRelease(
        records=[
            {"files": [{"uri": uri_a}]},
            {"files": [{"uri": uri_b}]},
        ]
    )
    fake_a = MagicMock(uri=uri_a)
    fake_b = MagicMock(uri=uri_b)
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        mock_fi.query.filter.return_value.all.return_value = [fake_a, fake_b]
        errors = validator.validate(release)
    assert len(errors) == 1
    assert uri_a in errors[0]
    assert uri_b in errors[0]


def test_validate_staged_release_skips_check():
    validator = CheckDuplicateFiles()
    release = DummyRelease(
        records=[{"files": [{"uri": "root://eos.cern.ch/file1.root"}]}],
        status="STAGED",
    )
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        errors = validator.validate(release)
    mock_fi.query.filter.assert_not_called()
    assert errors == []


def test_validate_published_release_skips_check():
    validator = CheckDuplicateFiles()
    release = DummyRelease(
        records=[{"files": [{"uri": "root://eos.cern.ch/file1.root"}]}],
        status="PUBLISHED",
    )
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        errors = validator.validate(release)
    mock_fi.query.filter.assert_not_called()
    assert errors == []


def test_validate_release_without_status_catches_duplicate_uris():
    validator = CheckDuplicateFiles()
    uri = "root://eos.cern.ch/file1.root"
    release = DummyRelease(records=[{"files": [{"uri": uri}]}], status=None)
    fake_file = MagicMock(uri=uri)
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        mock_fi.query.filter.return_value.all.return_value = [fake_file]
        errors = validator.validate(release)
    assert len(errors) == 1
    assert uri in errors[0]


def test_validate_ready_release_catches_duplicate_uris():
    validator = CheckDuplicateFiles()
    uri = "root://eos.cern.ch/file1.root"
    release = DummyRelease(
        records=[{"files": [{"uri": uri}]}],
        status="READY",
    )
    fake_file = MagicMock(uri=uri)
    with patch(
        "cernopendata.modules.releases.validations.duplicate_files.FileInstance"
    ) as mock_fi:
        mock_fi.query.filter.return_value.all.return_value = [fake_file]
        errors = validator.validate(release)
    assert len(errors) == 1
    assert uri in errors[0]
