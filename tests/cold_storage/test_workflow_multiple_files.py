import logging
from unittest.mock import patch

import pytest

from cernopendata.cold_storage.cli import cold

from .utils import assert_list_output, run_command

LIMIT_TEST_CASES = [
    pytest.param(
        {
            "recid": "1116",
            "title": "Multi-File Record for Negative Limit Test",
            "file_specs": [
                {"name": "data1.txt", "content": b"Content for data file 1."},
                {"name": "data2.txt", "content": b"Content for data file 2."},
                {"name": "data3.txt", "content": b"Content for data file 3."},
            ],
        },
        {
            "archive": -1,
            "clear": -1,
            "stage": -2,
        },
        {
            "initial": (3, 0),
            "after_archive": (3, 2),
            "after_clear": (1, 2),
            "after_stage": (2, 2),
        },
    ),
    pytest.param(
        {
            "recid": "1117",
            "title": "Multi-File Record for Positive Limit Test",
            "file_specs": [
                {"name": "data4.txt", "content": b"Content for data file 1."},
                {"name": "data5.txt", "content": b"Content for data file 2."},
                {"name": "data6.txt", "content": b"Content for data file 3."},
            ],
        },
        {"archive": 1, "clear": 1, "stage": 2},
        {
            "initial": (3, 0),
            "after_archive": (3, 1),
            "after_clear": (2, 1),
            "after_stage": (3, 1),
        },
    ),
]


@pytest.mark.parametrize("record_data, limits, expected", LIMIT_TEST_CASES)
@patch(
    "cernopendata.cold_storage.manager.Storage.verify_file", return_value=(False, None)
)
def test_cold_storage_workflow_with_limits(
    mock_verify, app, cli_runner, record_factory, record_data, limits, expected, caplog
):
    """
    Tests the complete cold storage workflow with limits.
    """
    caplog.set_level(logging.INFO)
    record = record_factory(record_data)
    record_id = record["id"]

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result, record["hot_paths"], record["cold_paths"], *expected["initial"]
    )

    run_command(
        cli_runner,
        app,
        cold,
        ["archive", record_id, "--limit", limits["archive"], "--register"],
    )

    excpected_transfers = (
        limits["archive"]
        if limits["archive"] > 0
        else len(record["hot_paths"]) + limits["archive"]
    )

    # testing logged output of 'cernopendata cold transfers'
    result = run_command(cli_runner, app, cold, ["transfers"])
    if limits["archive"] > 0:
        for i, file_path in enumerate(record["cold_paths"][0 : limits["archive"]]):
            assert file_path in caplog.records[-1 - i].msg
    else:
        for i, file_path in enumerate(record["cold_paths"][limits["archive"] : 0]):
            assert file_path in caplog.records[-1 - excpected_transfers + i].msg

    # testing logged output of 'cernopendata cold process-transfers'
    run_command(cli_runner, app, cold, ["process-transfers"])
    assert f"Summary: {{'DONE': {excpected_transfers}}}" in caplog.records[-1].msg

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result, record["hot_paths"], record["cold_paths"], *expected["after_archive"]
    )

    run_command(
        cli_runner, app, cold, ["clear-hot", record_id, "--limit", limits["clear"]]
    )

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result, record["hot_paths"], record["cold_paths"], *expected["after_clear"]
    )

    run_command(
        cli_runner,
        app,
        cold,
        ["stage", record_id, "--register", "--limit", limits["stage"]],
    )
    run_command(cli_runner, app, cold, ["process-transfers"])

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(
        result, record["hot_paths"], record["cold_paths"], *expected["after_stage"]
    )
