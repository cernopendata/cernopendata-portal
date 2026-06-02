from unittest.mock import MagicMock, patch

from cernopendata.modules.releases.models import ReleaseStatus
from cernopendata.modules.releases.validations.recid import ValidRecid


class DummyRelease:
    def __init__(self, records=None, status="DRAFT", experiment="CMS", max_recid=0):
        self.records = records or []
        self.status = ReleaseStatus[status].value if status else None
        self.experiment = experiment
        self.max_recid = max_recid


def test_validate_passes_with_unique_recids():
    validator = ValidRecid()
    release = DummyRelease(records=[{"recid": "CMS-1"}, {"recid": "CMS-2"}])
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert errors == []


def test_validate_reports_missing_recid():
    validator = ValidRecid()
    release = DummyRelease(records=[{"title": "no recid"}])
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert any("Missing" in e for e in errors)
    assert any("recid" in e for e in errors)


def test_validate_reports_duplicate_recid():
    validator = ValidRecid()
    release = DummyRelease(records=[{"recid": "CMS-1"}, {"recid": "CMS-1"}])
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert any("Duplicate" in e for e in errors)
    assert any("CMS-1" in e for e in errors)


def test_validate_reports_already_registered_recid():
    validator = ValidRecid()
    release = DummyRelease(records=[{"recid": "CMS-1"}])
    with patch.object(validator, "_duplicate_pids", return_value=["CMS-1"]):
        errors = validator.validate(release)
    assert any("already registered" in e for e in errors)


def test_validate_staged_release_skips_pid_check():
    validator = ValidRecid()
    release = DummyRelease(records=[{"recid": "CMS-1"}], status="STAGED")
    spy = MagicMock(return_value=[])
    validator._duplicate_pids = spy
    errors = validator.validate(release)
    spy.assert_not_called()
    assert errors == []


def test_validate_no_records_returns_no_errors():
    validator = ValidRecid()
    release = DummyRelease(records=[])
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert errors == []


def test_next_recid_start_returns_one_when_no_existing():
    validator = ValidRecid()
    release = DummyRelease()
    with patch("cernopendata.modules.releases.validations.recid.db") as mock_db:
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = (
            None
        )
        result = validator.next_recid_start(release)
    assert result == 1


def test_next_recid_start_returns_max_plus_one():
    validator = ValidRecid()
    release = DummyRelease()
    with patch("cernopendata.modules.releases.validations.recid.db") as mock_db:
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 42
        result = validator.next_recid_start(release)
    assert result == 43


def test_fix_assigns_recid_to_record_without_one():
    validator = ValidRecid()
    record = {"title": "no recid"}
    release = DummyRelease(records=[record], experiment="CMS", max_recid=10)
    with patch.object(validator, "next_recid_start", return_value=10), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ):
        errors = validator.fix(release)
    assert errors == []
    assert record["recid"] == "CMS-11"


def test_fix_reassigns_duplicate_recid():
    validator = ValidRecid()
    record_a = {"recid": "CMS-1"}
    record_b = {"recid": "CMS-1"}
    release = DummyRelease(records=[record_a, record_b], experiment="CMS", max_recid=5)
    with patch.object(validator, "next_recid_start", return_value=5), patch.object(
        validator, "_duplicate_pids", return_value=["CMS-1"]
    ):
        errors = validator.fix(release)
    assert errors == []
    assert record_a["recid"] == "CMS-6"
    assert record_b["recid"] == "CMS-7"


def test_fix_preserves_non_duplicate_recid():
    validator = ValidRecid()
    record = {"recid": "CMS-5"}
    release = DummyRelease(records=[record], experiment="CMS", max_recid=10)
    with patch.object(validator, "next_recid_start", return_value=10), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ):
        errors = validator.fix(release)
    assert errors == []
    assert record["recid"] == "CMS-5"


def test_fix_updates_max_recid():
    validator = ValidRecid()
    record = {"title": "no recid"}
    release = DummyRelease(records=[record], experiment="CMS", max_recid=0)
    with patch.object(validator, "next_recid_start", return_value=3), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ):
        validator.fix(release)
    assert release.max_recid == 4


def test_fix_no_records_does_not_update_max_recid():
    validator = ValidRecid()
    release = DummyRelease(records=[], experiment="CMS", max_recid=0)
    with patch.object(validator, "next_recid_start", return_value=1), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ):
        errors = validator.fix(release)
    assert errors == []
    assert release.max_recid == 0
