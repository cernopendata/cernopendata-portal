from unittest.mock import patch

import pytest

from cernopendata.cold_storage.cli import cold
from cernopendata.cold_storage.storage import Storage
from cernopendata.modules.fixtures.cli import create_record

from .utils import assert_list_output, build_record, run_command

MULTIPLE_FILE_RECORDS = [
    {
        "recid": "1116",
        "title": "Multi-File Record for Limit Test",
        "file_specs": [
            {"name": "data1.txt", "content": b"Content for data file 1."},
            {"name": "data2.txt", "content": b"Content for data file 2."},
            {"name": "data3.txt", "content": b"Content for data file 3."},
        ],
    },
]


@pytest.mark.parametrize("record_data", MULTIPLE_FILE_RECORDS)
def test_cold_storage_workflow_with_limits(
    app,
    database,
    cli_runner,
    storage_paths,
    setup_location,
    record_data,
):
    """
    Tests the complete cold storage workflow with limits.
    """
    record_id, hot_file_paths, cold_file_paths, record_dict = build_record(
        app, storage_paths, record_data
    )
    record = create_record(record_dict, False)
    record.commit()

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 3, 0)
    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_command(
            cli_runner, app, cold, ["archive", record_id, "--limit", -1, "--register"]
        )
        run_command(cli_runner, app, cold, ["process-transfers"])

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 3, 2)

    run_command(cli_runner, app, cold, ["clear-hot", record_id, "--limit", -1])
    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 2)

    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_command(
            cli_runner, app, cold, ["stage", record_id, "--register", "--limit", -2]
        )
        run_command(cli_runner, app, cold, ["process-transfers"])

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 2, 2)
