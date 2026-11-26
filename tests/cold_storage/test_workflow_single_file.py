import logging
from unittest.mock import patch

import pytest
from invenio_files_rest.models import ObjectVersionTag
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.cold_storage.cli import cold
from cernopendata.modules.fixtures.cli import update_record

from .utils import assert_list_output, build_record_with_files, run_command

SINGLE_FILE_RECORDS = [
    {
        "recid": "1114",
        "title": "File Record",
        "file_specs": [
            {"name": "file.txt", "content": b"This is a dummy file for testing."}
        ],
    },
    {
        "recid": "1115",
        "title": "Index Record",
        "file_specs": [
            {
                "name": "index.json",
                "type": "index.json",
                "referenced_file_info": {
                    "name": "index_file.txt",
                    "content": b"This is a dummy file for testing referenced by the index.",
                },
            }
        ],
    },
]


@pytest.mark.parametrize("record_data", SINGLE_FILE_RECORDS)
@patch(
    "cernopendata.cold_storage.manager.Storage.verify_file", return_value=(False, None)
)
def test_cold_storage_workflow(
    mock_verify, app, cli_runner, record_factory, record_data, caplog
):
    """
    Tests the complete cold storage workflow for records with either a file or an index file.
    """
    caplog.set_level(logging.INFO)
    record = record_factory(record_data)
    record_id = record["id"]

    result = run_command(cli_runner, app, cold, ["location", "list"])
    assert "/cold_storage" in result.output
    assert "/hot_storage" in result.output

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result,
        record["hot_paths"],
        record["cold_paths"],
        expected_hot_count=1,
        expected_cold_count=0,
    )

    run_command(cli_runner, app, cold, ["archive", record_id, "--register"])

    result = run_command(cli_runner, app, cold, ["transfers"])
    assert record["cold_paths"][0] in caplog.records[-1].msg

    result = run_command(cli_runner, app, cold, ["process-transfers"])
    assert "Summary: {'DONE': 1}" in caplog.records[-1].msg

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result,
        record["hot_paths"],
        record["cold_paths"],
        expected_hot_count=1,
        expected_cold_count=1,
    )

    run_command(cli_runner, app, cold, ["clear-hot", record_id])
    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result,
        record["hot_paths"],
        record["cold_paths"],
        expected_hot_count=0,
        expected_cold_count=1,
    )

    run_command(cli_runner, app, cold, ["stage", record_id, "--register"])
    run_command(cli_runner, app, cold, ["process-transfers"])

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result,
        record["hot_paths"],
        record["cold_paths"],
        expected_hot_count=1,
        expected_cold_count=1,
    )


def _reload_file_specs(recid):
    return [
        {
            "name": f"reload_file_{recid}.txt",
            "content": b"This is a dummy file for reloading.",
        },
        {
            "name": "index.json",
            "type": "index.json",
            "referenced_file_info": {
                "name": f"reload_index_file_{recid}.txt",
                "content": b"This is a dummy file referenced by the reloaded index.",
            },
        },
    ]


COLD_TAGS = {"uri_cold": "root://cold/copy", "hot_deleted": "2026-01-01 00:00:00"}


def _create_cold_record(app, database, storage_paths, record_factory, recid):
    record_data = {
        "recid": recid,
        "title": "Cold Record",
        "file_specs": _reload_file_specs(recid),
    }
    record = record_factory(record_data)["record_obj"]
    version_ids = [record_file["version_id"] for record_file in record["_files"]]
    for file_index in record["_file_indices"]:
        version_ids += [
            index_entry["version_id"] for index_entry in file_index["files"]
        ]
    for version_id in version_ids:
        for tag_key, tag_value in COLD_TAGS.items():
            ObjectVersionTag.create(version_id, tag_key, tag_value)
    record.files.flush()
    record.flush_indices()
    record.commit()
    database.session.commit()
    _, _, _, update_data = build_record_with_files(
        app,
        storage_paths,
        {
            "recid": recid,
            "title": "Reloaded Record",
            "file_specs": _reload_file_specs(recid),
        },
    )
    return PersistentIdentifier.get("recid", recid), update_data


def test_update_record_preserves_cold_tags(
    app, database, storage_paths, record_factory
):
    pid, update_data = _create_cold_record(
        app, database, storage_paths, record_factory, "1160"
    )

    updated_record = update_record(pid, update_data, False)

    assert updated_record["title"] == "Reloaded Record"
    assert updated_record["availability"] == "on demand"
    assert updated_record["_availability_details"] == {"on demand": 2}
    assert updated_record["_files"][0]["tags"] == COLD_TAGS
    assert updated_record["_files"][0]["availability"] == "on demand"
    assert updated_record["files"][0]["availability"] == "on demand"
    assert updated_record["_file_indices"][0]["availability"] == {"on demand": 1}
    assert updated_record["_file_indices"][0]["files"][0]["tags"] == COLD_TAGS


def test_update_record_drops_cold_tags_of_changed_file(
    app, database, storage_paths, record_factory
):
    pid, update_data = _create_cold_record(
        app, database, storage_paths, record_factory, "1161"
    )
    update_data["files"][0]["checksum"] = "adler32:00000000"

    updated_record = update_record(pid, update_data, False)

    assert updated_record["availability"] == "partial"
    assert updated_record["_files"][0]["tags"] == {}
    assert updated_record["_files"][0]["availability"] == "online"
    assert updated_record["_file_indices"][0]["files"][0]["tags"] == COLD_TAGS


def test_update_record_skip_files_keeps_availability(
    app, database, storage_paths, record_factory
):
    pid, update_data = _create_cold_record(
        app, database, storage_paths, record_factory, "1162"
    )

    updated_record = update_record(pid, update_data, True)

    assert updated_record["title"] == "Reloaded Record"
    assert updated_record["availability"] == "on demand"
    assert updated_record["_availability_details"] == {"on demand": 2}
