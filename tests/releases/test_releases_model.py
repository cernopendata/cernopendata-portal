from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release, ReleaseValidation
from cernopendata.modules.releases.models import ReleaseStatus


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
        release = None

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
