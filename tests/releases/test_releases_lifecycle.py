from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from cernopendata.modules.releases.api import Release, ReleaseValidation
from cernopendata.modules.releases.models import ReleaseStatus


def test_create_success(mocker, mock_jsonschemas):
    """Test the creation of a release."""
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_validate = mocker.patch("cernopendata.modules.releases.api.Release.validate")

    mock_release_metadata = MagicMock()
    mocker.patch(
        "cernopendata.modules.releases.api.ReleaseMetadata",
        return_value=mock_release_metadata,
    )

    user = MagicMock()

    records = [{"a": 1}]
    Release.create(
        experiment="cms",
        records=records,
        current_user=user,
        name="test",
    )

    assert records[0]["$schema"] == "schema-url"
    mock_validate.assert_called_once()
    assert mock_session.add.called
    mock_session.commit.assert_called_once()


def test_lock_success(mocker, mock_metadata):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(id=1, status="DRAFT")
    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    user = MagicMock()

    result = r.lock(
        status=True, lock_status=MagicMock(value="EDITING"), current_user=user
    )

    assert result is True
    mock_session.commit.assert_called_once()


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


def test_stage_success(mocker, mock_jsonschemas, mock_metadata):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_create = mocker.patch("cernopendata.modules.releases.api.create_record")
    mocker.patch("cernopendata.modules.releases.api.create_doc")

    mock_record = MagicMock()
    mock_create.return_value = mock_record

    metadata = mock_metadata(
        records=[{"recid": 1}], experiment="cms", id=1, num_errors=0
    )
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


def test_publish(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")

    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(records=[{"recid": 1}])
    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    mock_session.commit.assert_called_once()


def test_rollback(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.delete_record")

    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(records=[{"recid": 1}])
    r = Release(metadata)

    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.rollback(MagicMock())

    mock_session.commit.assert_called_once()


def test_create_with_documents(mocker, mock_jsonschemas):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.Release.validate")
    mock_release_metadata = mocker.patch(
        "cernopendata.modules.releases.api.ReleaseMetadata"
    )

    doc = {"slug": "alice-about", "body": {"content": "# About", "format": "md"}}

    Release.create(
        experiment="cms",
        documents=[doc],
        current_user=MagicMock(),
        name="docs-release.json",
    )

    assert doc["$schema"] == "schema-url"
    mock_session.commit.assert_called_once()
    _, kwargs = mock_release_metadata.call_args
    assert kwargs["documents"] == [doc]
    assert kwargs["records"] == []
    assert kwargs["num_docs"] == 1


def test_create_defaults_to_empty_lists(mocker):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.Release.validate")
    mock_release_metadata = mocker.patch(
        "cernopendata.modules.releases.api.ReleaseMetadata"
    )

    Release.create(experiment="cms", current_user=MagicMock(), name="empty.json")

    _, kwargs = mock_release_metadata.call_args
    assert kwargs["records"] == []
    assert kwargs["documents"] == []
    assert kwargs["num_docs"] == 0


def test_stage_with_errors_reverts_to_draft(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(num_errors=2)
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mock_change = mocker.patch.object(r, "change_status")

    with pytest.raises(RuntimeError, match="validation errors"):
        r.stage(MagicMock())

    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, mocker.ANY)


def test_stage_with_documents(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_create_record = mocker.patch("cernopendata.modules.releases.api.create_record")
    mock_create_doc = mocker.patch("cernopendata.modules.releases.api.create_doc")

    mock_create_record.return_value = MagicMock()
    mock_create_doc.return_value = MagicMock()

    metadata = mock_metadata(
        documents=[
            {"slug": "my-doc", "_source_filename": "my-doc.json", "title": "My Doc"}
        ],
        experiment="cms",
        id=42,
        num_errors=0,
    )
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.stage(MagicMock())

    mock_create_doc.assert_called_once()
    call_arg = mock_create_doc.call_args[0][0]
    assert "_source_filename" not in call_arg
    assert call_arg["prerelease"] == "cms/42"
    assert call_arg["$schema"] == "schema-url"


def test_publish_with_documents(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_update_doc = mocker.patch(
        "cernopendata.modules.releases.api.update_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.db.session")

    mock_doc = MagicMock()
    mock_update_doc.return_value = mock_doc

    metadata = mock_metadata(
        documents=[
            {
                "slug": "my-doc",
                "_source_filename": "my-doc.json",
                "prerelease": "cms/42",
                "$schema": "schema-url",
            }
        ]
    )
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


def test_rollback_with_documents(mocker, mock_metadata):
    mock_pid_get = mocker.patch(
        "cernopendata.modules.releases.api.PersistentIdentifier.get"
    )
    mock_delete_doc = mocker.patch(
        "cernopendata.modules.releases.api.delete_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.delete_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(documents=[{"slug": "my-doc"}])
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.rollback(MagicMock())

    mock_pid_get.assert_called_with("docid", "my-doc")
    mock_delete_doc.assert_called_once()


def test_rollback_skips_doc_without_slug(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mock_delete_doc = mocker.patch(
        "cernopendata.modules.releases.api.delete_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.delete_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(documents=[{"title": "no slug here"}])
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


def test_stage_with_errors_commits_draft_status(mocker, mock_metadata):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(num_errors=1)
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mock_change = mocker.patch.object(r, "change_status")

    user = MagicMock()
    with pytest.raises(RuntimeError, match="validation errors"):
        r.stage(user)

    mock_change.assert_called_once_with(ReleaseStatus.DRAFT, user)
    mock_session.commit.assert_called_once()


def test_publish_preserves_schema_on_each_record(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(
        records=[
            {"recid": 1, "$schema": "schema-url"},
            {"recid": 2, "$schema": "schema-url"},
        ]
    )
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    assert all(rec["$schema"] == "schema-url" for rec in metadata.records)


def test_publish_raises_when_document_missing_slug(
    mocker, mock_jsonschemas, mock_metadata
):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(documents=[{"title": "no slug here"}])
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    with pytest.raises(RuntimeError, match="missing 'slug'"):
        r.publish(MagicMock())


def test_publish_commits_each_document(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_update_doc = mocker.patch(
        "cernopendata.modules.releases.api.update_doc_or_glossary"
    )
    mocker.patch("cernopendata.modules.releases.api.db.session")

    docs = [MagicMock(), MagicMock()]
    mock_update_doc.side_effect = docs

    metadata = mock_metadata(documents=[{"slug": "doc-a"}, {"slug": "doc-b"}])
    r = Release(metadata)
    mocker.patch.object(r, "is_status", return_value=True)
    mocker.patch.object(r, "change_status")

    r.publish(MagicMock())

    for doc in docs:
        doc.commit.assert_called_once()


def test_delete_removes_uploaded_images(mocker, tmp_path, mock_metadata):
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

    metadata = mock_metadata(id=1)
    r = Release(metadata)
    r.delete()

    assert not release_dir.exists()
    assert (tmp_path / "2" / "doc-a" / "fig.png").exists()
    mock_session.delete.assert_called_once_with(metadata)
    mock_session.commit.assert_called_once()


def test_delete_release_images_oserror_logs_and_continues(
    mocker, tmp_path, mock_metadata
):
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"CERNOPENDATA_IMAGES_PATH": str(tmp_path)}
    mock_current_app.logger = MagicMock()

    release_dir = tmp_path / "1"
    release_dir.mkdir()

    mocker.patch(
        "cernopendata.modules.releases.api.shutil.rmtree", side_effect=OSError("locked")
    )

    metadata = mock_metadata(id=1)
    r = Release(metadata)
    r._delete_release_images()

    mock_current_app.logger.warning.assert_called_once()
    assert release_dir.exists()


def test_generate_doi_mints_missing_dois(mocker, mock_metadata):
    mock_mint = mocker.patch(
        "cernopendata.modules.releases.api.mint_doi", return_value="10.1234/NEW"
    )
    mocker.patch("cernopendata.modules.releases.api.validate_datacite_record")
    mock_flag = mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"PIDSTORE_DATACITE_DOI_PREFIX": "10.1234"}

    metadata = mock_metadata(
        records=[
            {"recid": 1},
            {"recid": 2, "doi": "10.1234/EXISTING"},
        ],
        experiment="CMS",
    )
    release = Release(metadata)
    errors = release.generate_doi([1])

    assert metadata.records[0]["doi"] == "10.1234/NEW"
    assert metadata.records[1]["doi"] == "10.1234/EXISTING"
    mock_mint.assert_called_once_with("10.1234", "CMS")
    mock_flag.assert_called_once_with(metadata, "records")
    assert errors == []


def test_generate_doi_returns_validation_errors(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.mint_doi")
    mock_validate = mocker.patch(
        "cernopendata.modules.releases.api.validate_datacite_record"
    )
    mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {}

    mock_validate.side_effect = [None, ValueError("bad field")]

    metadata = mock_metadata(
        records=[{"recid": 1}, {"recid": 2}],
        experiment="CMS",
    )
    release = Release(metadata)
    errors = release.generate_doi([1, 2])

    assert len(errors) == 1
    assert errors[0]["recid"] == 2
    assert "bad field" in errors[0]["error"]
    assert "doi" not in metadata.records[1]


def test_generate_doi_skips_records_not_in_recids(mocker, mock_metadata):
    mock_mint = mocker.patch(
        "cernopendata.modules.releases.api.mint_doi", return_value="10.1234/NEW"
    )
    mocker.patch("cernopendata.modules.releases.api.validate_datacite_record")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.config = {"PIDSTORE_DATACITE_DOI_PREFIX": "10.1234"}

    metadata = mock_metadata(
        records=[{"recid": 1}, {"recid": 2}],
        experiment="CMS",
    )
    release = Release(metadata)
    errors = release.generate_doi([1])

    assert metadata.records[0].get("doi") == "10.1234/NEW"
    assert "doi" not in metadata.records[1]
    mock_mint.assert_called_once()
    assert errors == []


def test_publish_collects_datacite_errors(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_register = mocker.patch(
        "cernopendata.modules.releases.api.register_record_doi"
    )
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_current_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_current_app.logger = MagicMock()

    mock_register.side_effect = [None, RuntimeError("DataCite down")]

    metadata = mock_metadata(
        records=[
            {"recid": 1, "doi": "10.1234/A"},
            {"recid": 2, "doi": "10.1234/B"},
        ]
    )
    release = Release(metadata)
    mocker.patch.object(release, "is_status", return_value=True)
    mocker.patch.object(release, "change_status")

    errors = release.publish(MagicMock())

    assert len(errors) == 1
    assert errors[0]["recid"] == 2
    assert "DataCite down" in errors[0]["error"]
    mock_session.commit.assert_called_once()


def test_publish_skips_registration_when_record_has_no_doi(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.RecordIndexer")
    mocker.patch("cernopendata.modules.releases.api.PersistentIdentifier.get")
    mocker.patch("cernopendata.modules.releases.api.update_record")
    mock_register = mocker.patch(
        "cernopendata.modules.releases.api.register_record_doi"
    )
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(records=[{"recid": 1}])
    release = Release(metadata)
    mocker.patch.object(release, "is_status", return_value=True)
    mocker.patch.object(release, "change_status")

    release.publish(MagicMock())

    mock_register.assert_not_called()
