from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release


def test_update_records(mocker, mock_jsonschemas, mock_metadata):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata()
    r = Release(metadata)

    mock_validate = mocker.patch.object(r, "validate")

    record = {"a": 1}
    r.update_records([record], MagicMock())

    assert record["$schema"] == "schema-url"
    assert metadata.records == [record]
    mock_validate.assert_called_once()
    mock_session.commit.assert_called_once()


def test_bulk_preview(mock_metadata):
    metadata = mock_metadata(records=[{"recid": 1, "a": 1}])
    r = Release(metadata)

    diffs = r.bulk_preview({"set": {"a": 2}})

    assert len(diffs) == 1
    assert diffs[0]["recid"] == 1


def test_bulk_update(mocker, mock_metadata):
    mock_session = mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_flag = mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(records=[{"a": 1}])
    r = Release(metadata)

    mocker.patch.object(r, "validate")

    count = r.bulk_update({"set": {"a": 2}}, MagicMock())

    assert count == 1
    assert metadata.records[0]["a"] == 2
    mock_session.commit.assert_called_once()


def test_bulk_preview_respects_max_preview(mock_metadata):
    metadata = mock_metadata(
        records=[{"recid": 1, "a": 1}, {"recid": 2, "a": 1}, {"recid": 3, "a": 1}]
    )
    release = Release(metadata)

    diffs = release.bulk_preview({"set": {"a": 2}}, max_preview=2)

    assert [diff["index"] for diff in diffs] == [0, 1]


def test_bulk_preview_skips_immutable_fields(mock_metadata):
    metadata = mock_metadata(records=[{"recid": 1, "title": "Original", "year": 2010}])
    release = Release(metadata)

    diffs = release.bulk_preview(
        {"set": {"recid": 99, "title": "Changed", "year": 2020}}
    )

    assert len(diffs) == 1
    serialized_diff = str(diffs[0]["diff"])
    assert "2020" in serialized_diff
    assert "99" not in serialized_diff
    assert "Changed" not in serialized_diff


def test_bulk_preview_delete_operation(mock_metadata):
    metadata = mock_metadata(records=[{"recid": 1, "obsolete": "drop me"}])
    release = Release(metadata)

    diffs = release.bulk_preview({"delete": ["obsolete"]})

    assert len(diffs) == 1
    assert diffs[0]["recid"] == 1


def test_bulk_update_delete_removes_field(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(records=[{"recid": 1, "obsolete": "drop me"}])
    release = Release(metadata)
    mocker.patch.object(release, "validate")

    count = release.bulk_update({"delete": ["obsolete"]}, MagicMock())

    assert count == 1
    assert "obsolete" not in metadata.records[0]


def test_bulk_update_skips_immutable_fields(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_flag_modified = mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(records=[{"recid": 1, "title": "Original"}])
    release = Release(metadata)
    mocker.patch.object(release, "validate")

    count = release.bulk_update({"set": {"recid": 99, "title": "Changed"}}, MagicMock())

    assert count == 0
    assert metadata.records[0] == {"recid": 1, "title": "Original"}
    mock_flag_modified.assert_not_called()


def test_bulk_update_no_changes_skips_flag_modified(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mock_flag_modified = mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(records=[{"recid": 1}])
    release = Release(metadata)
    mocker.patch.object(release, "validate")

    count = release.bulk_update({"delete": ["nonexistent"]}, MagicMock())

    assert count == 0
    mock_flag_modified.assert_not_called()


def test_add_records_triggers_validate(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata()
    r = Release(metadata)
    mock_validate = mocker.patch.object(r, "validate")

    user = MagicMock()
    r.add_records([{"recid": 1}], user)

    mock_validate.assert_called_once_with(user)


def test_add_records_sets_schema_on_each_record(
    mocker, mock_jsonschemas, mock_metadata
):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata()
    r = Release(metadata)
    mocker.patch.object(r, "validate")

    new_records = [{"recid": 1}, {"recid": 2}]
    r.add_records(new_records, MagicMock())

    assert all(rec["$schema"] == "schema-url" for rec in new_records)


def test_add_records_appends_to_existing_records(
    mocker, mock_jsonschemas, mock_metadata
):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(records=[{"recid": 1, "title": "Existing"}])
    r = Release(metadata)
    mocker.patch.object(r, "validate")

    r.add_records(
        [{"recid": 2, "title": "New A"}, {"recid": 3, "title": "New B"}], MagicMock()
    )

    assert len(metadata.records) == 3
    assert [rec["recid"] for rec in metadata.records] == [1, 2, 3]


def test_add_records_to_release_with_no_records(mocker, mock_jsonschemas):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = MagicMock()
    metadata.records = None

    r = Release(metadata)
    mocker.patch.object(r, "validate")

    r.add_records([{"recid": 1}], MagicMock())

    assert metadata.records == [{"recid": 1, "$schema": "schema-url"}]
