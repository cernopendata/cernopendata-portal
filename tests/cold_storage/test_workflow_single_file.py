import logging
from unittest.mock import patch

import pytest

from cernopendata.cold_storage.cli import cold

from .utils import assert_list_output, run_command

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
