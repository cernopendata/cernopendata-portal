from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release
from cernopendata.modules.releases.models import ReleaseStatus


def test_validate(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    r = Release(metadata)
    user = MagicMock()
    r.validate(user)
    r.fix_checks(user)


def test_validate_catches_validator_crash_and_records_synthetic_error(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")

    metadata = MagicMock()
    metadata.records = []

    r = Release(metadata)

    crashing_validation = MagicMock(enabled=True)
    crashing_validation.name = "BrokenValidator"
    crashing_validation.validate.side_effect = RuntimeError("unexpected crash")
    mocker.patch.object(
        Release, "validations", new_callable=mocker.PropertyMock
    ).return_value = [crashing_validation]

    mock_change = mocker.patch.object(r, "change_status")

    r.validate(MagicMock())

    mock_current_app.logger.error.assert_called_once()
    assert any("BrokenValidator" in e for e in metadata.errors)
    assert any("unexpected error" in e for e in metadata.errors)
    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, mocker.ANY)


def test_validate_with_errors_sets_status_draft(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = MagicMock()
    metadata.records = []
    metadata.validations = []

    r = Release(metadata)

    failing_validation = MagicMock(enabled=True)
    failing_validation.validate.return_value = ["bad field"]
    mocker.patch.object(
        Release, "validations", new_callable=mocker.PropertyMock
    ).return_value = [failing_validation]

    mock_change = mocker.patch.object(r, "change_status")

    r.validate(MagicMock())

    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, mocker.ANY)
