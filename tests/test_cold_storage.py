import json
import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from invenio_files_rest.models import Location

from cernopendata.cold_storage.cli import cold, location
from cernopendata.cold_storage.storage import Storage
from cernopendata.modules.fixtures.cli import create_record

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


@pytest.fixture(scope="module")
def cli_runner():
    """Provides a Click CliRunner instance."""
    return CliRunner()


@pytest.fixture(scope="module")
def storage_paths(tmp_path_factory):
    """
    Provides hot and cold storage paths within a temporary directory.
    """
    base_tmp_path = tmp_path_factory.mktemp("cold_storage_module_base")
    hot_path = base_tmp_path / "hot_storage"
    cold_path = base_tmp_path / "cold_storage"
    os.makedirs(hot_path, exist_ok=True)
    os.makedirs(cold_path, exist_ok=True)
    return hot_path, cold_path


@pytest.fixture(scope="module")
def setup_location(cli_runner, app, database, storage_paths):
    """Sets up the storage locations in the database and via CLI."""
    hot_path, cold_path = storage_paths
    manager_class = "cernopendata.cold_storage.transfer.cp.TransferManager"

    record_location = Location(name="local", uri=str(hot_path), default=True)
    database.session.add(record_location)
    database.session.commit()

    result = cli_runner.invoke(
        location,
        [
            "add",
            "--cold-path",
            str(cold_path),
            "--hot-path",
            str(hot_path),
            "--manager-class",
            manager_class,
        ],
        obj=app,
    )
    assert result.exit_code == 0
    assert "Location added with ID" in result.output
    return str(hot_path), str(cold_path), manager_class


def _build_record(app, storage_paths, record_data_param):
    """
    Constructs a record dictionary and creates associated dummy files.
    """
    hot_path, cold_path = storage_paths

    files_list_for_record = []
    hot_file_paths = []
    cold_file_paths = []

    for spec in record_data_param["file_specs"]:
        file_name = spec["name"]
        file_type = spec.get("type")

        is_index = file_name == "index.json" and "referenced_file_info" in spec

        if is_index:
            referenced_info = spec["referenced_file_info"]
            ref_file_name = referenced_info["name"]
            ref_file_content = referenced_info["content"]

            ref_hot_path = hot_path / ref_file_name
            ref_hot_path.write_bytes(ref_file_content)

            index_content_data = [
                {
                    "checksum": "adler32:9719fd6a",
                    "size": len(ref_file_content),
                    "uri": str(ref_hot_path),
                }
            ]
            file_content_for_current_spec = json.dumps(index_content_data).encode(
                "utf-8"
            )
        else:
            file_content_for_current_spec = spec["content"]

        hot_file_path = hot_path / file_name
        hot_file_path.write_bytes(file_content_for_current_spec)

        file_entry_dict = {
            "checksum": "adler32:9719fd6a",
            "size": len(file_content_for_current_spec),
            "uri": str(hot_file_path),
        }
        if file_type:
            file_entry_dict["type"] = file_type

        files_list_for_record.append(file_entry_dict)
        hot_file_paths.append(str(ref_hot_path) if is_index else str(hot_file_path))
        cold_file_paths.append(
            str(cold_path / ref_file_name) if is_index else str(cold_path / file_name)
        )

    record_dict = {
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            record_data_param.get("schema_path", "records/record-v1.0.0.json")
        ),
        "recid": record_data_param["recid"],
        "date_published": "2024",
        "experiment": ["ALICE"],
        "publisher": "CERN Open Data Portal",
        "title": record_data_param["title"],
        "type": {
            "primary": "Dataset",
            "secondary": ["Derived"],
        },
        "files": files_list_for_record,
    }

    return (
        record_data_param["recid"],
        hot_file_paths,
        cold_file_paths,
        record_dict,
    )


def run_cli_command(runner, app, command, args):
    """Helper to run a CLI command and assert success."""
    result = runner.invoke(command, args, obj=app)
    assert result.exit_code == 0
    return result


def assert_list_output(
    result,
    hot_file_paths,
    cold_file_paths,
    expected_hot_count,
    expected_cold_count,
):
    """
    Asserts common elements in the 'cold list' output.
    """
    assert result.exit_code == 0
    assert f"Summary: {len(hot_file_paths)} files" in result.output

    actual_hot_count = 0
    for hot_path in hot_file_paths:
        if f"Hot copy: {hot_path}" in result.output:
            actual_hot_count += 1
        else:
            assert f"Hot copy: {hot_path}" not in result.output

    assert actual_hot_count == expected_hot_count
    assert f"{expected_hot_count} hot copies" in result.output

    actual_cold_count = 0
    for cold_path_str in cold_file_paths:
        if f"Cold copy: {cold_path_str}" in result.output:
            actual_cold_count += 1
        else:
            assert f"Cold copy: {cold_path_str}" not in result.output

    assert actual_cold_count == expected_cold_count
    assert f"{expected_cold_count} cold copies" in result.output


@pytest.mark.parametrize("record_data", SINGLE_FILE_RECORDS)
def test_cold_storage_workflow(
    app, database, cli_runner, storage_paths, setup_location, record_data
):
    """
    Tests the complete cold storage workflow for records with either a file or an index file.
    """
    record_id, hot_file_paths, cold_file_paths, record_dict = _build_record(
        app, storage_paths, record_data
    )

    record = create_record(record_dict, False)
    record.commit()

    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 0)

    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_cli_command(cli_runner, app, cold, ["archive", record_id, "--register"])
        run_cli_command(cli_runner, app, cold, ["process-transfers"])

    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 1)

    run_cli_command(cli_runner, app, cold, ["clear-hot", record_id])
    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 0, 1)

    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_cli_command(cli_runner, app, cold, ["stage", record_id, "--register"])
        run_cli_command(cli_runner, app, cold, ["process-transfers"])

    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 1)


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
    record_id, hot_file_paths, cold_file_paths, record_dict = _build_record(
        app, storage_paths, record_data
    )
    record = create_record(record_dict, False)
    record.commit()

    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 3, 0)
    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_cli_command(
            cli_runner, app, cold, ["archive", record_id, "--limit", -1, "--register"]
        )
        run_cli_command(cli_runner, app, cold, ["process-transfers"])

    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 3, 2)

    run_cli_command(cli_runner, app, cold, ["clear-hot", record_id, "--limit", -1])
    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 2)

    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_cli_command(
            cli_runner, app, cold, ["stage", record_id, "--register", "--limit", -2]
        )
        run_cli_command(cli_runner, app, cold, ["process-transfers"])

    result = run_cli_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 2, 2)
