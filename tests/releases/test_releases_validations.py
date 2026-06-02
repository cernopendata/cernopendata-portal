from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release
from cernopendata.modules.releases.models import ReleaseStatus


def test_validate_catches_validator_crash_and_records_synthetic_error(
    mocker, mock_metadata
):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.logger = MagicMock()

    metadata = mock_metadata()

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


def test_validate_with_errors_sets_status_draft(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(validations=[])
    r = Release(metadata)

    failing_validation = MagicMock(enabled=True)
    failing_validation.validate.return_value = ["bad field"]
    mocker.patch.object(
        Release, "validations", new_callable=mocker.PropertyMock
    ).return_value = [failing_validation]

    mock_change = mocker.patch.object(r, "change_status")

    r.validate(MagicMock())

    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, mocker.ANY)


def test_fix_checks_runs_fix_then_revalidates_when_no_errors(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata()
    release = Release(metadata)

    fixable_validation = MagicMock(status=False, enabled=True, fixable=True)
    fixable_validation.fix.return_value = []
    mocker.patch.object(
        Release, "validations", new_callable=mocker.PropertyMock
    ).return_value = [fixable_validation]

    mock_validate = mocker.patch.object(release, "validate")
    mock_change = mocker.patch.object(release, "change_status")

    release.fix_checks(MagicMock())

    fixable_validation.fix.assert_called_once()
    mock_validate.assert_called_once()
    mock_change.assert_not_called()


def test_fix_checks_with_unfixable_errors_sets_draft(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata()
    release = Release(metadata)

    failing_validation = MagicMock(status=False, enabled=True, fixable=True)
    failing_validation.fix.return_value = ["still broken"]
    mocker.patch.object(
        Release, "validations", new_callable=mocker.PropertyMock
    ).return_value = [failing_validation]

    mock_validate = mocker.patch.object(release, "validate")
    mock_change = mocker.patch.object(release, "change_status")

    release.fix_checks(MagicMock())

    assert metadata.errors == ["still broken"]
    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, mocker.ANY)
    mock_validate.assert_not_called()


def test_fix_checks_skips_passing_validations(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata()
    release = Release(metadata)

    passing_validation = MagicMock(status=True, enabled=True, fixable=True)
    mocker.patch.object(
        Release, "validations", new_callable=mocker.PropertyMock
    ).return_value = [passing_validation]

    mocker.patch.object(release, "validate")

    release.fix_checks(MagicMock())

    passing_validation.fix.assert_not_called()


def test_enable_validation_toggles_optional_validation(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata()
    release = Release(metadata)

    validation = MagicMock(optional=True)
    validation._metadata = MagicMock()
    mocker.patch(
        "cernopendata.modules.releases.api.ReleaseValidation.get",
        return_value=validation,
    )
    mock_validate = mocker.patch.object(release, "validate")

    release.enable_validation(validation_id=5, enabled=False, current_user=MagicMock())

    assert validation._metadata.enabled is False
    mock_validate.assert_called_once()


def test_enable_validation_rejects_required_validation(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    release = Release(mock_metadata())

    validation = MagicMock(optional=False)
    mocker.patch(
        "cernopendata.modules.releases.api.ReleaseValidation.get",
        return_value=validation,
    )

    with pytest.raises(RuntimeError, match="can't be disabled"):
        release.enable_validation(
            validation_id=5, enabled=False, current_user=MagicMock()
        )
