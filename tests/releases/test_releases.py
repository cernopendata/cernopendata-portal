from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release, ReleaseValidation
from cernopendata.modules.releases.models import (
    ReleaseMetadata,
    ReleaseStatus,
    ReleaseValidationMetadata,
)
from cernopendata.modules.releases.validations.base import Validation


@pytest.fixture
def dummy_metadata():
    """Return a fresh ReleaseMetadata object for tests."""
    return ReleaseMetadata(
        name="dummy_release",
        experiment="cms",
        records=[],
        validations=[],
        status=ReleaseStatus.DRAFT.value,
    )


# -----------------------------
# TEST ReleaseValidation
# -----------------------------


def test_release_validation():
    """Check a release validation object."""

    class ReleaseValidationMetadata:
        id = 1
        release_id = 2
        name = "Duplicate files"
        status = "OK"
        enabled = True

    release_validation = ReleaseValidation(ReleaseValidationMetadata())

    assert release_validation.name == "Duplicate files"
    assert release_validation.validator
    assert not release_validation.fixable
    assert release_validation.error_message
    assert release_validation.status == "OK"
    release_validation.set_status("FAILED")
    assert release_validation.status == "FAILED"
    assert release_validation.to_dict()


def test_release_properties(dummy_metadata):
    """Test Release object properties."""

    release = Release(dummy_metadata)
    assert release.status == dummy_metadata.status
    assert release.records == dummy_metadata.records
    assert len(release.validations) == 0


def test_validate_experiment():
    """Test that experiment name is valid."""
    assert Release.validate_experiment("cms")
    assert not Release.validate_experiment("invalid")


def test_create_success(mocker):
    """Test the creation of a release."""
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_validate = mocker.patch("cernopendata.modules.releases.api.Release.validate")

    mock_metadata = MagicMock()
    mocker.patch(
        "cernopendata.modules.releases.api.ReleaseMetadata",
        return_value=mock_metadata,
    )

    user = MagicMock()

    release = Release.create(
        experiment="cms",
        records=[{"a": 1}],
        current_user=user,
        name="test",
    )

    mock_validate.assert_called_once()
    assert mock_session.add.called
    mock_session.commit.assert_called_once()
    assert release


def test_is_status():
    metadata = MagicMock()
    metadata.status = ReleaseStatus.DRAFT.value

    r = Release(metadata)

    assert r.is_status(ReleaseStatus.DRAFT)


def test_lock_success(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.id = 1
    metadata.status = "DRAFT"

    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    user = MagicMock()

    result = r.lock(
        status=True, lock_status=MagicMock(value="EDITING"), current_user=user
    )

    assert result is True
    mock_session.commit.assert_called_once()


from sqlalchemy.exc import OperationalError


def test_lock_operational_error(mocker):
    mock_query = mocker.patch("cernopendata.modules.releases.api.db.session.query")

    mock_query.return_value.filter_by.return_value.with_for_update.return_value.one.side_effect = OperationalError(
        "", "", ""
    )

    r = Release(MagicMock(id=1))

    result = r.lock(status=None, lock_status=None, current_user=MagicMock())

    assert result is False


def test_delete(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    r = Release(metadata)

    r.delete()

    mock_session.delete.assert_called_once_with(metadata)
    mock_session.commit.assert_called_once()


def test_validate(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    r = Release(metadata)
    user = MagicMock()
    r.validate(user)
    r.fix_checks(user)


def test_update_records(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    r = Release(metadata)

    mock_validate = mocker.patch.object(r, "validate")

    r.update_records([{"a": 1}], MagicMock())

    assert metadata.records == [{"a": 1}]
    mock_validate.assert_called_once()
    mock_session.commit.assert_called_once()


def test_bulk_preview():
    metadata = MagicMock()
    metadata.records = [{"recid": 1, "a": 1}]

    r = Release(metadata)

    diffs = r.bulk_preview({"set": {"a": 2}})

    assert len(diffs) == 1
    assert diffs[0]["recid"] == 1


def test_bulk_update(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_flag = mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = MagicMock()
    metadata.records = [{"a": 1}]

    r = Release(metadata)

    mocker.patch.object(r, "validate")

    count = r.bulk_update({"set": {"a": 2}}, MagicMock())

    assert count == 1
    assert metadata.records[0]["a"] == 2
    mock_session.commit.assert_called_once()


def test_stage_success(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_create = mocker.patch("cernopendata.modules.releases.api.create_record")

    mock_record = MagicMock()
    mock_create.return_value = mock_record

    metadata = MagicMock()
    metadata.records = [{"recid": 1}]
    metadata.experiment = "cms"
    metadata.id = 1

    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.stage("schema", MagicMock())

    mock_record.commit.assert_called()


import pytest


def test_stage_wrong_status(mocker):
    r = Release(MagicMock())

    mocker.patch.object(r, "is_status", return_value=False)

    with pytest.raises(RuntimeError):
        r.stage("schema", MagicMock())


def test_publish(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")

    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.records = [{"recid": 1}]

    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    mock_session.commit.assert_called_once()


def test_rollback(mocker):
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.delete_record")

    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.records = [{"recid": 1}]

    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.rollback(MagicMock())

    mock_session.commit.assert_called_once()
