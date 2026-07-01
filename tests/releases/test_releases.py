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


def test_create_success(mocker):
    """Test the creation of a release."""
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_validate = mocker.patch("cernopendata.modules.releases.api.Release.validate")

    mock_metadata = MagicMock()
    mocker.patch(
        "cernopendata.modules.releases.api.ReleaseMetadata",
        return_value=mock_metadata,
    )

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    user = MagicMock()

    records = [{"a": 1}]
    release = Release.create(
        experiment="cms",
        records=records,
        current_user=user,
        name="test",
    )

    assert records[0]["$schema"] == "schema-url"
    mock_validate.assert_called_once()
    assert mock_session.add.called
    mock_session.commit.assert_called_once()
    assert release


def test_create_validations_filters_by_experiment(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    class FakeValidation:
        def __init__(self, name, experiment):
            self.name = name
            self.experiment = experiment
            self.optional = False

    mocker.patch(
        "cernopendata.modules.releases.api.VALIDATIONS",
        [
            FakeValidation("all-experiments", None),
            FakeValidation("cms-only", "cms"),
            FakeValidation("cms-and-atlas", {"cms", "atlas"}),
            FakeValidation("lhcb-only", "lhcb"),
        ],
    )

    metadata = ReleaseMetadata(
        name="atlas_release",
        experiment="atlas",
        records=[],
        validations=[],
        status=ReleaseStatus.DRAFT.value,
    )
    Release(metadata).create_validations()

    created = {validation.name for validation in metadata.validations}
    assert created == {"all-experiments", "cms-and-atlas"}


def test_is_status():
    metadata = MagicMock()
    metadata.status = ReleaseStatus.DRAFT.value

    r = Release(metadata)

    assert r.is_status(ReleaseStatus.DRAFT)


def test_lock_success(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.id = 1
    metadata.status = ReleaseStatus.DRAFT.value

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
    metadata.status = ReleaseStatus.DRAFT.value
    r.delete()

    mock_session.delete.assert_called_once_with(metadata)
    mock_session.commit.assert_called_once()


def test_failed_delete(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    r = Release(metadata)
    metadata.status = "PUBLISHED"
    with pytest.raises(
        RuntimeError, match="Releases can be deleted only if they are in DRAFT or READY"
    ):
        r.delete()


def test_validate(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    r = Release(metadata)
    user = MagicMock()
    r.validate(user)
    r.fix_checks(user)


def test_update_records(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    r = Release(metadata)

    mock_validate = mocker.patch.object(r, "validate")

    record = {"a": 1}
    r.update_records([record], MagicMock())

    assert record["$schema"] == "schema-url"
    assert metadata.records == [record]
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
    mocker.patch("cernopendata.modules.releases.api.create_doc")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    mock_record = MagicMock()
    mock_create.return_value = mock_record

    metadata = MagicMock()
    metadata.records = [{"recid": 1}]
    metadata.documents = []
    metadata.experiment = "cms"
    metadata.id = 1
    metadata.num_errors = 0

    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.stage(MagicMock())

    mock_record.commit.assert_called()


def test_stage_wrong_status(mocker):
    r = Release(MagicMock())

    mocker.patch.object(r, "is_status", return_value=False)

    with pytest.raises(RuntimeError):
        r.stage(MagicMock())


def test_publish(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.records = [{"recid": 1}]
    metadata.documents = []

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


def test_add_documents_triggers_validate(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.documents = []
    metadata.num_docs = 0

    r = Release(metadata)
    mock_validate = mocker.patch.object(r, "validate")

    user = MagicMock()
    r.add_documents([{"slug": "alice-data-2015"}], user)

    mock_validate.assert_called_once_with(user)


def test_add_documents_updates_count(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.documents = [{"slug": "existing-doc"}]
    metadata.num_docs = 1

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    r.add_documents([{"slug": "new-doc-1"}, {"slug": "new-doc-2"}], MagicMock())

    assert metadata.num_docs == 3
    assert len(metadata.documents) == 3


def test_add_documents_accepts_large_list(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.documents = []
    metadata.num_docs = 0

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    large_batch = [{"slug": f"doc-{i}"} for i in range(500)]
    r.add_documents(large_batch, MagicMock())

    assert metadata.num_docs == 500
    assert len(metadata.documents) == 500


def test_update_document_success(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.documents = [{"slug": "alice-data-2015", "title": "Old Title"}]

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    updated = {"slug": "alice-data-2015", "title": "New Title"}
    r.update_document("alice-data-2015", updated, MagicMock())

    assert metadata.documents[0]["title"] == "New Title"


def test_update_document_not_found(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.documents = [{"slug": "existing-doc"}]

    r = Release(metadata)

    with pytest.raises(ValueError, match="not found"):
        r.update_document("nonexistent-slug", {"slug": "nonexistent-slug"}, MagicMock())


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


def test_create_with_documents(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.Release.validate")
    mock_metadata = mocker.patch("cernopendata.modules.releases.api.ReleaseMetadata")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    doc = {"slug": "alice-about", "body": {"content": "# About", "format": "md"}}

    release = Release.create(
        experiment="cms",
        documents=[doc],
        current_user=MagicMock(),
        name="docs-release.json",
    )

    assert release
    assert doc["$schema"] == "schema-url"
    mock_session.commit.assert_called_once()
    _, kwargs = mock_metadata.call_args
    assert kwargs["documents"] == [doc]
    assert kwargs["records"] == []
    assert kwargs["num_docs"] == 1


def test_create_defaults_to_empty_lists(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.Release.validate")
    mock_metadata = mocker.patch("cernopendata.modules.releases.api.ReleaseMetadata")

    Release.create(experiment="cms", current_user=MagicMock(), name="empty.json")

    _, kwargs = mock_metadata.call_args
    assert kwargs["records"] == []
    assert kwargs["documents"] == []
    assert kwargs["num_docs"] == 0


def test_stage_with_errors_reverts_to_draft(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.num_errors = 2

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mock_change = mocker.patch.object(r, "change_status")

    with pytest.raises(RuntimeError, match="validation errors"):
        r.stage(MagicMock())

    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, mocker.ANY)


def test_stage_with_documents(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_create_record = mocker.patch("cernopendata.modules.releases.api.create_record")
    mock_create_doc = mocker.patch("cernopendata.modules.releases.api.create_doc")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    mock_create_record.return_value = MagicMock()
    mock_create_doc.return_value = MagicMock()

    metadata = MagicMock()
    metadata.records = []
    metadata.documents = [
        {"slug": "my-doc", "_source_filename": "my-doc.json", "title": "My Doc"}
    ]
    metadata.experiment = "cms"
    metadata.id = 42
    metadata.num_errors = 0

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.stage(MagicMock())

    mock_create_doc.assert_called_once()
    call_arg = mock_create_doc.call_args[0][0]
    assert "_source_filename" not in call_arg
    assert call_arg["prerelease"] == "cms/42"
    assert call_arg["$schema"] == "schema-url"


def test_publish_with_documents(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_update_doc = mocker.patch(
        "cernopendata.modules.releases.api.update_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_doc = MagicMock()
    mock_update_doc.return_value = mock_doc

    metadata = MagicMock()
    metadata.records = []
    metadata.documents = [
        {
            "slug": "my-doc",
            "_source_filename": "my-doc.json",
            "prerelease": "cms/42",
            "$schema": "schema-url",
        }
    ]

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    mock_update_doc.assert_called_once()
    call_arg = mock_update_doc.call_args[0][1]
    assert "_source_filename" not in call_arg
    assert "prerelease" not in call_arg
    assert call_arg["$schema"] == "schema-url"
    mock_doc.commit.assert_called_once()


def test_rollback_with_documents(mocker):
    mock_pid_get = mocker.patch(
        "cernopendata.modules.releases.api.PersistentIdentifier.get"
    )
    mock_delete_doc = mocker.patch(
        "cernopendata.modules.releases.api.delete_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.delete_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.records = []
    metadata.documents = [{"slug": "my-doc"}]

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.rollback(MagicMock())

    mock_pid_get.assert_called_with("docid", "my-doc")
    mock_delete_doc.assert_called_once()


def test_rollback_skips_doc_without_slug(mocker):
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mock_delete_doc = mocker.patch(
        "cernopendata.modules.releases.api.delete_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.delete_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.records = []
    metadata.documents = [{"title": "no slug here"}]

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.rollback(MagicMock())

    mock_delete_doc.assert_not_called()


def test_create_raises_when_records_not_list(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.ReleaseMetadata")

    with pytest.raises(ValueError, match="must be lists"):
        Release.create(
            experiment="cms",
            records={"not": "a list"},
            current_user=MagicMock(),
        )


def test_create_raises_when_documents_not_list(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.ReleaseMetadata")

    with pytest.raises(ValueError, match="must be lists"):
        Release.create(
            experiment="cms",
            records=[],
            documents="not a list",
            current_user=MagicMock(),
        )


def test_stage_with_errors_commits_draft_status(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.num_errors = 1

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mock_change = mocker.patch.object(r, "change_status")

    user = MagicMock()
    with pytest.raises(RuntimeError, match="validation errors"):
        r.stage(user)

    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, user)
    mock_session.commit.assert_called_once()


def test_mark_staging_failed_records_error_and_reverts_to_ready(mocker):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = MagicMock()
    r = Release(metadata)
    mock_change = mocker.patch.object(r, "change_status")

    user = MagicMock()
    r.mark_staging_failed("Broken release", user)

    assert metadata.errors == ["Staging failed: Broken release"]
    assert metadata.num_errors == 1
    mock_change.assert_called_once_with(ReleaseStatus.READY, user)
    mock_session.commit.assert_called_once()


def test_publish_preserves_schema_on_each_record(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = MagicMock()
    metadata.records = [
        {"recid": 1, "$schema": "schema-url"},
        {"recid": 2, "$schema": "schema-url"},
    ]
    metadata.documents = []

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    assert all(rec["$schema"] == "schema-url" for rec in metadata.records)


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


def test_publish_raises_when_document_missing_slug(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.records = []
    metadata.documents = [{"title": "no slug here"}]

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    with pytest.raises(RuntimeError, match="missing 'slug'"):
        r.publish(MagicMock())


def test_publish_commits_each_document(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_update_doc = mocker.patch(
        "cernopendata.modules.releases.api.update_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    docs = [MagicMock(), MagicMock()]
    mock_update_doc.side_effect = docs

    metadata = MagicMock()
    metadata.records = []
    metadata.documents = [{"slug": "doc-a"}, {"slug": "doc-b"}]

    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    for doc in docs:
        doc.commit.assert_called_once()


def test_delete_removes_uploaded_images(mocker, tmp_path):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"CERNOPENDATA_IMAGES_PATH": str(tmp_path)}

    release_dir = tmp_path / "1"
    (release_dir / "doc-a").mkdir(parents=True)
    (release_dir / "doc-a" / "fig.png").write_bytes(b"a")
    (release_dir / "doc-b").mkdir()
    (release_dir / "doc-b" / "fig.png").write_bytes(b"b")
    (tmp_path / "2" / "doc-a").mkdir(parents=True)
    (tmp_path / "2" / "doc-a" / "fig.png").write_bytes(b"other-release")

    metadata = MagicMock()
    metadata.id = 1
    metadata.status = ReleaseStatus.DRAFT.value

    r = Release(metadata)
    r.delete()

    assert not release_dir.exists()
    assert (tmp_path / "2" / "doc-a" / "fig.png").exists()
    mock_session.delete.assert_called_once_with(metadata)
    mock_session.commit.assert_called_once()


def test_delete_release_images_oserror_logs_and_continues(mocker, tmp_path):
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"CERNOPENDATA_IMAGES_PATH": str(tmp_path)}

    release_dir = tmp_path / "1"
    release_dir.mkdir()

    mocker.patch(
        "cernopendata.modules.releases.api.shutil.rmtree", side_effect=OSError("locked")
    )

    metadata = MagicMock()
    metadata.id = 1

    r = Release(metadata)
    r._delete_release_images()

    mock_current_app.logger.warning.assert_called_once()
    assert release_dir.exists()


def test_delete_release_images_no_directory_does_nothing(mocker, tmp_path):
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"CERNOPENDATA_IMAGES_PATH": str(tmp_path)}

    metadata = MagicMock()
    metadata.id = 1

    r = Release(metadata)
    r._delete_release_images()


def test_add_records_triggers_validate(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.records = []

    r = Release(metadata)
    mock_validate = mocker.patch.object(r, "validate")

    user = MagicMock()
    r.add_records([{"recid": 1}], user)

    mock_validate.assert_called_once_with(user)


def test_add_records_sets_schema_on_each_record(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.records = []

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    new_records = [{"recid": 1}, {"recid": 2}]
    r.add_records(new_records, MagicMock())

    assert all(rec["$schema"] == "schema-url" for rec in new_records)


def test_add_records_appends_to_existing_records(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.records = [{"recid": 1, "title": "Existing"}]

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    r.add_records(
        [{"recid": 2, "title": "New A"}, {"recid": 3, "title": "New B"}], MagicMock()
    )

    assert len(metadata.records) == 3
    assert [rec["recid"] for rec in metadata.records] == [1, 2, 3]


def test_add_records_to_release_with_no_records(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }

    metadata = MagicMock()
    metadata.records = None

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    r.add_records([{"recid": 1}], MagicMock())

    assert metadata.records == [{"recid": 1, "$schema": "schema-url"}]


def test_generate_doi_mints_missing_dois(mocker):
    mock_mint = mocker.patch(
        "cernopendata.modules.releases.api.mint_doi", return_value="10.1234/NEW"
    )
    mocker.patch("cernopendata.modules.releases.api.validate_datacite_record")
    mock_flag = mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"PIDSTORE_DATACITE_DOI_PREFIX": "10.1234"}

    metadata = MagicMock()
    metadata.experiment = "CMS"
    metadata.records = [
        {"recid": 1},
        {"recid": 2, "doi": "10.1234/EXISTING"},
        {"recid": 3},
    ]

    release = Release(metadata)
    errors = release.generate_doi([1, 2])

    assert metadata.records[0]["doi"] == "10.1234/NEW"
    assert metadata.records[1]["doi"] == "10.1234/EXISTING"
    assert "doi" not in metadata.records[2]
    mock_mint.assert_called_once_with("10.1234", "CMS")
    mock_flag.assert_called_once_with(metadata, "records")
    assert errors == []


def test_generate_doi_returns_validation_errors(mocker):
    mocker.patch("cernopendata.modules.releases.api.mint_doi")
    mock_validate = mocker.patch(
        "cernopendata.modules.releases.api.validate_datacite_record"
    )
    mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {}

    mock_validate.side_effect = [None, ValueError("bad field")]

    metadata = MagicMock()
    metadata.experiment = "CMS"
    metadata.records = [
        {"recid": 1},
        {"recid": 2},
    ]

    release = Release(metadata)
    errors = release.generate_doi([1, 2])

    assert len(errors) == 1
    assert errors[0]["recid"] == 2
    assert "bad field" in errors[0]["error"]
    assert "doi" not in metadata.records[1]


def test_publish_collects_datacite_errors(mocker):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_register = mocker.patch(
        "cernopendata.modules.releases.api.register_record_doi"
    )
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.current_app")

    mock_register.side_effect = [None, RuntimeError("DataCite down")]

    metadata = MagicMock()
    metadata.records = [
        {"recid": 1, "doi": "10.1234/A"},
        {"recid": 2, "doi": "10.1234/B"},
        {"recid": 3},
    ]
    metadata.documents = []

    release = Release(metadata)
    mocker.patch.object(release, "is_status", return_value=True)
    mocker.patch.object(release, "change_status")

    errors = release.publish(MagicMock())

    assert len(errors) == 1
    assert errors[0]["recid"] == 2
    assert "DataCite down" in errors[0]["error"]
    assert mock_register.call_count == 2
    mock_session.commit.assert_called_once()
