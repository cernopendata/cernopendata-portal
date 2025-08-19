from unittest.mock import patch

import pytest
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.cold_storage.api import Request
from cernopendata.cold_storage.cli import cold
from cernopendata.cold_storage.models import RequestMetadata
from cernopendata.cold_storage.storage import Storage
from cernopendata.modules.fixtures.cli import create_record

from .utils import assert_list_output, build_record, run_command

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
def test_cold_storage_workflow(
    app, database, cli_runner, storage_paths, setup_location, record_data
):
    """
    Tests the complete cold storage workflow for records with either a file or an index file.
    """
    record_id, hot_file_paths, cold_file_paths, record_dict = build_record(
        app, storage_paths, record_data
    )

    record = create_record(record_dict, False)
    record.commit()

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 0)

    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_command(cli_runner, app, cold, ["archive", record_id, "--register"])
        run_command(cli_runner, app, cold, ["process-transfers"])

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 1)

    run_command(cli_runner, app, cold, ["clear-hot", record_id])
    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 0, 1)

    with patch(
        "cernopendata.cold_storage.manager.Storage.verify_file",
        return_value=(True, None),
    ):
        run_command(cli_runner, app, cold, ["stage", record_id, "--register"])
        run_command(cli_runner, app, cold, ["process-transfers"])

    result = run_command(cli_runner, app, cold, ["list", record_id])
    assert_list_output(result, hot_file_paths, cold_file_paths, 1, 1)


def test_subscribe(app, database):
    """
    Tests a subscribtion to a transfer
    """
    s = PersistentIdentifier.query.first()
    request = Request.create(s.object_uuid, None)
    database.session.add(request)
    database.session.commit()

    # test a successful subscription
    subscriber = "new@domain.com"
    result = Request.subscribe(request.id, subscriber)
    assert result is True
    request_md = RequestMetadata.query.filter_by(id=request.id).first()
    assert subscriber in request_md.subscribers

    # test trying to subscribe when already subscribed
    result = Request.subscribe(request.id, subscriber)
    assert result is False
    request_md = RequestMetadata.query.filter_by(id=request.id).first()
    assert subscriber in request_md.subscribers
    assert len(request_md.subscribers) == 1
