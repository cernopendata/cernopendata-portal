from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release, ReleaseValidation
from cernopendata.modules.releases.models import ReleaseStatus


class _DuplicateFilesMetadata:
    id = 1
    release_id = 2
    name = "Duplicate files"
    status = "OK"
    enabled = True
    release = None


def test_release_validation():
    """Check a release validation object."""
    release_validation = ReleaseValidation(_DuplicateFilesMetadata())

    assert release_validation.name == "Duplicate files"
    assert release_validation.validator is not None
    assert not release_validation.fixable
    assert (
        release_validation.error_message
        == "Some of the files of the records are already registered"
    )
    assert release_validation.status == "OK"
    result = release_validation.to_dict()
    assert result["id"] == 1
    assert result["name"] == "Duplicate files"
    assert result["status"] == "OK"
    assert result["release_id"] == 2


def test_release_validation_set_status():
    """Check that set_status mutates the status field."""
    release_validation = ReleaseValidation(_DuplicateFilesMetadata())

    release_validation.set_status("FAILED")

    assert release_validation.status == "FAILED"


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


def test_is_status():
    metadata = MagicMock()
    metadata.status = ReleaseStatus.DRAFT.value

    r = Release(metadata)

    assert r.is_status(ReleaseStatus.DRAFT)


def test_release_documents_property():
    metadata = MagicMock()
    metadata.documents = [{"slug": "doc-1"}]
    r = Release(metadata)
    assert r.documents == [{"slug": "doc-1"}]


def test_release_documents_property_returns_empty_list_when_none():
    metadata = MagicMock()
    metadata.documents = None
    r = Release(metadata)
    assert r.documents == []


def test_release_validation_is_document_validation():
    class DocValidationMetadata:
        id = 1
        release_id = 2
        name = "Valid slug"
        status = "OK"
        enabled = True

    rv = ReleaseValidation(DocValidationMetadata())
    assert rv.is_document_validation is True


def test_release_validation_is_not_document_validation():
    class RecordValidationMetadata:
        id = 1
        release_id = 2
        name = "Duplicate files"
        status = "OK"
        enabled = True

    rv = ReleaseValidation(RecordValidationMetadata())
    assert rv.is_document_validation is False


def test_release_validation_is_record_validation():
    class RecordValidationMetadata:
        id = 1
        release_id = 2
        name = "Duplicate files"
        status = "OK"
        enabled = True

    rv = ReleaseValidation(RecordValidationMetadata())
    assert rv.is_record_validation is True


def test_release_validation_is_not_record_validation_document_only():
    class DocValidationMetadata:
        id = 1
        release_id = 2
        name = "Valid slug"
        status = "OK"
        enabled = True

    rv = ReleaseValidation(DocValidationMetadata())
    assert rv.is_record_validation is False


def test_release_validation_is_not_record_validation_cross_cutting():
    class CrossValidationMetadata:
        id = 1
        release_id = 2
        name = "Valid experiment"
        status = "OK"
        enabled = True

    rv = ReleaseValidation(CrossValidationMetadata())
    assert rv.is_record_validation is False


def test_change_status_records_history_event(mocker, mock_metadata):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_history = mocker.patch("cernopendata.modules.releases.api.ReleaseHistory")

    metadata = mock_metadata()
    release = Release(metadata)
    user = MagicMock(id=7)

    event = release.change_status(ReleaseStatus.READY, user)

    assert metadata.status == ReleaseStatus.READY.value
    _, kwargs = mock_history.call_args
    assert kwargs["status"] == ReleaseStatus.READY.value
    assert kwargs["user_id"] == 7
    mock_session.add.assert_called_once_with(event)


def test_list_releases_filters_by_experiment(mocker):
    mock_query = mocker.patch("cernopendata.modules.releases.api.db.session.query")
    query_chain = (
        mock_query.return_value.options.return_value.filter.return_value.order_by.return_value
    )
    query_chain.all.return_value = ["release-a", "release-b"]

    result = Release.list_releases("cms")

    assert result == ["release-a", "release-b"]
    mock_query.assert_called_once()


def test_create_validations_appends_only_applicable_validations(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_validation_metadata = mocker.patch(
        "cernopendata.modules.releases.api.ReleaseValidationMetadata"
    )

    generic_validation = MagicMock(experiment=None, optional=False)
    generic_validation.name = "Generic"
    cms_validation = MagicMock(experiment="cms", optional=True)
    cms_validation.name = "CMS only"
    atlas_validation = MagicMock(experiment="atlas", optional=False)
    atlas_validation.name = "ATLAS only"

    mocker.patch(
        "cernopendata.modules.releases.api.VALIDATIONS",
        [generic_validation, cms_validation, atlas_validation],
    )

    metadata = mock_metadata(experiment="cms", validations=[])
    release = Release(metadata)
    release.create_validations()

    created_names = [
        kwargs["name"] for _, kwargs in mock_validation_metadata.call_args_list
    ]
    assert created_names == ["Generic", "CMS only"]
