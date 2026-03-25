import json
from datetime import datetime
from unittest.mock import patch

import pytest
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.modules.fixtures.cli import create_record, update_record
from cernopendata.tasks import (
    BATCH_SIZE,
    IGNORED_PATH,
    PREFIX,
    _get_existing_mapping_info,
    _path_to_id,
    _process_batch,
    _stream_dump_file,
    _update_last_accessed,
    process_eos_dump,
)


@pytest.fixture()
def mock_eos_dump(tmp_path):
    dump_data = [
        {
            "path": "/eos/opendata/cms/test_file.root",
            "adler32": "9719fd6a",
            "size": 1053,
            "mtime": 1774502519,
            "atime": 1774502518,
        },
        {
            "path": "/eos/opendata/cms/dark_file.root",
            "adler32": "test1234",
            "size": 500,
            "mtime": 1774502519,
            "atime": 1774502518,
        },
    ]
    dump_file = tmp_path / "test.dump"
    dump_file.write_text("\n".join(json.dumps(entry) for entry in dump_data))
    return str(dump_file)


@pytest.fixture(scope="module", autouse=True)
def task_indices(app, search):
    mapping_index = f"{app.config['SEARCH_INDEX_PREFIX']}records-recid_mapping"
    dark_index = f"{app.config['SEARCH_INDEX_PREFIX']}dark-files"

    for index, properties in [
        (
            mapping_index,
            {
                "uri": {"type": "keyword"},
                "recid": {"type": "keyword"},
                "title": {"type": "keyword"},
                "year_published": {"type": "date"},
                "timestamp": {"type": "date"},
                "last_accessed": {"type": "date"},
            },
        ),
        (
            dark_index,
            {
                "uri": {"type": "keyword"},
                "size": {"type": "long"},
                "adler32": {"type": "keyword"},
                "last_modified": {"type": "date"},
                "last_accessed": {"type": "date"},
            },
        ),
    ]:
        if not search.indices.exists(index=index):
            search.indices.create(
                index=index, body={"mappings": {"properties": properties}}
            )


def test_process_eos_dump(app, database, search, location, mock_eos_dump):
    path = "/eos/opendata/cms/test_file.root"
    full_uri = f"{PREFIX}{path}"

    data = {
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/record-v1.0.0.json"
        ),
        "recid": "1114",
        "date_published": "2024",
        "experiment": ["ALICE"],
        "publisher": "CERN Open Data Portal",
        "title": "Test record for EOS task",
        "type": {
            "primary": "Dataset",
            "secondary": ["Derived"],
        },
        "files": [{"checksum": "adler32:9719fd6a", "size": 1053, "uri": full_uri}],
    }

    create_record(data, False)
    db.session.commit()

    mapping_index = f"{app.config['SEARCH_INDEX_PREFIX']}records-recid_mapping"
    dark_index = f"{app.config['SEARCH_INDEX_PREFIX']}dark-files"

    with patch("cernopendata.tasks.EOS_DUMP_PATH", mock_eos_dump):
        process_eos_dump()
        search.indices.refresh()

        # Verify test_file was added to mapping index
        mapping_id = _path_to_id(path)
        assert search.exists(index=mapping_index, id=mapping_id)
        result = search.get(index=mapping_index, id=mapping_id)
        assert result["_source"]["recid"] == "1114"
        assert "last_accessed" in result["_source"]

        # Verify dark_file was added to dark-files index
        dark_path = "/eos/opendata/cms/dark_file.root"
        dark_file_id = _path_to_id(dark_path)
        assert search.exists(index=dark_index, id=dark_file_id)
        dark_result = search.get(index=dark_index, id=dark_file_id)
        assert dark_result["_source"]["adler32"] == "test1234"

        # Dark file is no longer dark
        path = f"{PREFIX}{dark_path}"
        data["files"].append(
            {
                "checksum": "adler32:test1234",
                "size": 500,
                "uri": path,
            }
        )

        pid = PersistentIdentifier.get("recid", data["recid"])
        update_record(pid, data, False)
        db.session.commit()

        process_eos_dump()
        search.indices.refresh()

        # Verify dark file was removed from dark-files index and added to mapping index
        assert not search.exists(index=dark_index, id=dark_file_id)
        assert search.exists(index=mapping_index, id=dark_file_id)
        result = search.get(index=mapping_index, id=dark_file_id)
        assert result["_source"]["recid"] == "1114"


def test_process_eos_dump_last_accessed_update(app, search, mock_eos_dump):
    mapping_index = f"{app.config['SEARCH_INDEX_PREFIX']}records-recid_mapping"
    path = "/eos/opendata/cms/test_file.root"
    doc_id = _path_to_id(path)

    search.index(
        index=mapping_index,
        id=doc_id,
        body={"uri": path, "recid": "1114", "last_accessed": "2020-01-01T00:00:00"},
    )
    search.indices.refresh()

    with patch("cernopendata.tasks.EOS_DUMP_PATH", mock_eos_dump):
        process_eos_dump()
        search.indices.refresh()

        # Verify last_accessed was updated
        result = search.get(index=mapping_index, id=doc_id)
        assert (
            result["_source"]["last_accessed"]
            == datetime.fromtimestamp(1774502518).isoformat()
        )


def test_process_eos_dump_skips_upload_paths(tmp_path):
    dump_data = [
        {"path": f"{IGNORED_PATH}some_file.root", "size": 100, "mtime": 0, "atime": 0},
        {"path": "/eos/opendata/valid_file.root", "size": 200, "mtime": 0, "atime": 0},
    ]
    dump_file = tmp_path / "test.dump"
    dump_file.write_text("\n".join(json.dumps(entry) for entry in dump_data))

    processed = []
    with patch("cernopendata.tasks.EOS_DUMP_PATH", str(dump_file)):
        with patch(
            "cernopendata.tasks._process_batch",
            side_effect=lambda args: processed.extend(args),
        ):
            process_eos_dump()

    # Verify the file with the /upload/ path was skipped
    assert len(processed) == 1
    assert processed[0]["path"] == "/eos/opendata/valid_file.root"


def test_process_eos_dump_batch_size(tmp_path):
    # Create entries for more that one batch
    entries = [
        {"path": f"/eos/opendata/file_{i}.root", "size": 1, "mtime": 0, "atime": 0}
        for i in range(BATCH_SIZE + 1)
    ]
    dump_file = tmp_path / "test.dump"
    dump_file.write_text("\n".join(json.dumps(e) for e in entries))

    batch_calls = []
    with patch("cernopendata.tasks.EOS_DUMP_PATH", str(dump_file)):
        with patch(
            "cernopendata.tasks._process_batch",
            side_effect=lambda args: batch_calls.append(len(args)),
        ):
            process_eos_dump()

    # Verify that entries were processed in two batches
    assert len(batch_calls) == 2
    assert batch_calls[0] == BATCH_SIZE
    assert batch_calls[1] == 1


def test_process_eos_dump_mid_batch_exception(tmp_path):
    entries = [
        {"path": f"/eos/opendata/file_{i}.root", "size": 1, "mtime": 0, "atime": 0}
        for i in range(BATCH_SIZE)
    ]
    dump_file = tmp_path / "test.dump"
    dump_file.write_text("\n".join(json.dumps(e) for e in entries))

    with patch("cernopendata.tasks.EOS_DUMP_PATH", str(dump_file)):
        with patch(
            "cernopendata.tasks._process_batch",
            side_effect=Exception("Failed to process batch"),
        ):
            # Verify that error is logged if the batch fails
            with patch("cernopendata.tasks.logger") as mock_logger:
                process_eos_dump()
                assert mock_logger.error.called


def test_process_eos_dump_batch_exception(mock_eos_dump):
    with patch("cernopendata.tasks.EOS_DUMP_PATH", mock_eos_dump):
        with patch(
            "cernopendata.tasks._process_batch",
            side_effect=Exception("Failed to process batch"),
        ):
            # Verify that error will be logged in case of failure to process batch
            with patch("cernopendata.tasks.logger") as mock_logger:
                process_eos_dump()
                assert mock_logger.error.called


def test_stream_dump_file_skips_invalid_json(tmp_path):
    dump_file = tmp_path / "test.dump"
    dump_file.write_text(
        "not valid json\n"
        '{"path": "/eos/opendata/valid.root", "size": 1, "mtime": 0, "atime": 0}\n'
        "also not json\n"
    )

    # Verify that invalid lines were skipped
    results = list(_stream_dump_file(str(dump_file)))
    assert len(results) == 1
    assert results[0]["path"] == "/eos/opendata/valid.root"


def test_process_batch_bulk_errors(app, search):
    entry = {"path": "/eos/opendata/file.root", "size": 1, "mtime": 0, "atime": 0}

    with patch("cernopendata.tasks._get_existing_mapping_info", return_value={}):
        with patch("cernopendata.tasks._get_records_by_paths", return_value=[]):
            with patch("cernopendata.tasks.search.helpers.bulk", return_value=(0, 1)):
                with patch("cernopendata.tasks.logger") as mock_logger:
                    # Verify that that error will be logged in case of empty results
                    _process_batch([entry])
                    assert mock_logger.error.called


def test_get_existing_mapping_info_empty():
    with patch("cernopendata.tasks.current_search_client") as mock_client:
        result = _get_existing_mapping_info([], "test-index")
        # Verify search will not be called in case of nothing in the index
        assert result == {}
        mock_client.search.assert_not_called()


def test_update_last_accessed_failure(app):
    mapping_index = f"{app.config['SEARCH_INDEX_PREFIX']}records-recid_mapping"
    entries = [{"path": "/eos/opendata/file.root", "atime": 0}]
    failed_result = {"failures": ["Test failure"], "updated": 0}
    with patch(
        "cernopendata.tasks.current_search_client.update_by_query",
        return_value=failed_result,
    ):
        # Verify that error will be logged if failure when updating last access dates
        with patch("cernopendata.tasks.logger") as mock_logger:
            _update_last_accessed(entries, mapping_index)
            assert mock_logger.error.called


def test_process_eos_dump_dark_file_last_accessed_update(app, search, tmp_path):
    dark_index = f"{app.config['SEARCH_INDEX_PREFIX']}dark-files"
    dark_path = "/eos/opendata/cms/dark_path_for_atime_test.root"
    doc_id = _path_to_id(dark_path)

    dump_file = tmp_path / "test.dump"
    dump_file.write_text(
        json.dumps(
            {
                "path": dark_path,
                "adler32": "abcd1234",
                "size": 500,
                "mtime": 1774502519,
                "atime": 1774502518,
            }
        )
    )

    search.index(
        index=dark_index,
        id=doc_id,
        body={
            "uri": dark_path,
            "size": 500,
            "adler32": "abcd1234",
            "last_modified": "2020-01-01T00:00:00",
            "last_accessed": "2020-01-01T00:00:00",
        },
    )
    search.indices.refresh()

    with patch("cernopendata.tasks.EOS_DUMP_PATH", str(dump_file)):
        process_eos_dump()
        search.indices.refresh()

        # Verify last_accessed was updated in the dark files index
        result = search.get(index=dark_index, id=doc_id)
        assert (
            result["_source"]["last_accessed"]
            == datetime.fromtimestamp(1774502518).isoformat()
        )


def test_get_existing_mapping_info_search_exception(mock_eos_dump):
    with patch("cernopendata.tasks.EOS_DUMP_PATH", mock_eos_dump):
        with patch(
            "cernopendata.tasks.current_search_client.search",
            side_effect=Exception("Connection error"),
        ):
            # Verify that failed search will cause an error to be logged
            with patch("cernopendata.tasks.logger") as mock_logger:
                process_eos_dump()
                assert mock_logger.error.called
