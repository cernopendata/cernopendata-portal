import json
import logging
from unittest.mock import patch

import pytest
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.cold_storage.api import Transfer
from cernopendata.cold_storage.cli import cold
from cernopendata.cold_storage.models import RequestMetadata

from .utils import run_command

SINGLE_FILE_RECORDS = [
    {
        "recid": "1114",
        "title": "File Record",
        "file_specs": [
            {"name": "file.txt", "content": b"This is a dummy file for testing."}
        ],
    },
    {
        "recid": "1116",
        "title": "Multi-File Record for Negative Limit Test",
        "file_specs": [
            {"name": "data1.txt", "content": b"Content for data file 1."},
            {"name": "data2.txt", "content": b"Content for data file 2."},
            {"name": "data3.txt", "content": b"Content for data file 3."},
        ],
    },
]


@pytest.mark.parametrize("record_data", SINGLE_FILE_RECORDS)
@patch(
    "cernopendata.cold_storage.manager.Storage.verify_file", return_value=(False, None)
)
def test_requests(
    mock_verify, client, app, cli_runner, record_factory, record_data, caplog
):
    caplog.set_level(logging.INFO)
    record = record_factory(record_data)
    recid = record["id"]

    run_command(cli_runner, app, cold, ["archive", recid, "--register"])
    run_command(cli_runner, app, cold, ["process-transfers"])
    run_command(cli_runner, app, cold, ["clear-hot", recid])

    with patch("cernopendata.modules.records.utils.RecordIndexer"):
        with patch("cernopendata.modules.records.utils.record_stage"):
            result = client.post(
                f"/record/{recid}/stage",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert result.status_code == 200

    result = run_command(cli_runner, app, cold, ["process-requests"])
    assert (
        f"{len(record_data['file_specs'])} transfers have been submitted!"
        in caplog.text
    )


@patch(
    "cernopendata.cold_storage.manager.Storage.verify_file", return_value=(False, None)
)
def test_request_with_failed_transfer(
    mock_verify, client, app, database, cli_runner, record_factory
):
    record = record_factory(
        {
            "recid": "1115",
            "title": "Test Record",
            "file_specs": [
                {"name": "file2.txt", "content": b"This is a dummy file for testing."}
            ],
        },
    )
    recid = record["id"]

    run_command(cli_runner, app, cold, ["archive", recid, "--register"])
    run_command(cli_runner, app, cold, ["process-transfers"])
    run_command(cli_runner, app, cold, ["clear-hot", recid])

    with patch("cernopendata.modules.records.utils.RecordIndexer"):
        with patch("cernopendata.modules.records.utils.record_stage"):
            result = client.post(
                f"/record/{recid}/stage",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert result.status_code == 200

    request = RequestMetadata.query.order_by(RequestMetadata.created_at.desc()).first()

    failed_transfer = Transfer.create(
        {
            "action": "stage",
            "new_filename": "test-file",
            "record_uuid": PersistentIdentifier.get("recid", recid).object_uuid,
            "request_id": request.id,
            "file_id": "test-file-id",
            "method": "test",
        }
    )
    failed_transfer.status = "FAILED"
    failed_transfer.finished = failed_transfer.submitted
    database.session.add(failed_transfer)
    database.session.commit()

    result = run_command(cli_runner, app, cold, ["process-requests"])

    request = RequestMetadata.query.order_by(RequestMetadata.created_at.desc()).first()
    assert request.num_failed_transfers == 1


@patch(
    "cernopendata.cold_storage.manager.Storage.verify_file", return_value=(False, None)
)
def test_request_ignores_other_failures(
    mock_verify, client, app, database, cli_runner, record_factory
):
    record = record_factory(
        {
            "recid": "1118",
            "title": "Test Record with Other Failures",
            "file_specs": [
                {"name": "file3.txt", "content": b"This is a dummy file for testing."}
            ],
        },
    )
    recid = record["id"]

    run_command(cli_runner, app, cold, ["archive", recid, "--register"])
    run_command(cli_runner, app, cold, ["process-transfers"])
    run_command(cli_runner, app, cold, ["clear-hot", recid])

    with patch("cernopendata.modules.records.utils.RecordIndexer"):
        with patch("cernopendata.modules.records.utils.record_stage"):
            result = client.post(
                f"/record/{recid}/stage",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert result.status_code == 200

    request = RequestMetadata.query.order_by(RequestMetadata.created_at.desc()).first()

    failed_transfer_of_another_request = Transfer.create(
        {
            "action": "stage",
            "new_filename": "test-file",
            "record_uuid": PersistentIdentifier.get("recid", recid).object_uuid,
            "request_id": request.id + 1000,
            "file_id": "test-file-id",
            "method": "test",
        }
    )
    failed_transfer_of_another_request.status = "FAILED"
    failed_transfer_of_another_request.finished = (
        failed_transfer_of_another_request.submitted
    )
    database.session.add(failed_transfer_of_another_request)
    database.session.commit()

    result = run_command(cli_runner, app, cold, ["process-requests"])

    request = RequestMetadata.query.order_by(RequestMetadata.created_at.desc()).first()
    assert request.num_failed_transfers == 0


@patch(
    "cernopendata.cold_storage.manager.Storage.verify_file", return_value=(False, None)
)
def test_request_size_counts_only_completed_transfers(
    mock_verify, client, app, database, cli_runner, record_factory
):
    record = record_factory(
        {
            "recid": "1119",
            "title": "Test Record with a Failed Transfer",
            "file_specs": [
                {"name": "file4.txt", "content": b"This is a dummy file for testing."}
            ],
        },
    )
    recid = record["id"]

    run_command(cli_runner, app, cold, ["archive", recid, "--register"])
    run_command(cli_runner, app, cold, ["process-transfers"])
    run_command(cli_runner, app, cold, ["clear-hot", recid])

    with patch("cernopendata.modules.records.utils.RecordIndexer"):
        with patch("cernopendata.modules.records.utils.record_stage"):
            result = client.post(
                f"/record/{recid}/stage",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert result.status_code == 200

    request = RequestMetadata.query.order_by(RequestMetadata.created_at.desc()).first()
    record_uuid = PersistentIdentifier.get("recid", recid).object_uuid

    completed_transfer = Transfer.create(
        {
            "action": "stage",
            "new_filename": "test-file",
            "record_uuid": record_uuid,
            "request_id": request.id,
            "file_id": "test-completed-file-id",
            "method": "test",
            "size": 1234,
        }
    )
    completed_transfer.status = "DONE"
    completed_transfer.finished = completed_transfer.submitted
    database.session.add(completed_transfer)

    failed_transfer = Transfer.create(
        {
            "action": "stage",
            "new_filename": "test-file",
            "record_uuid": record_uuid,
            "request_id": request.id,
            "file_id": "test-failed-file-id",
            "method": "test",
            "size": 5678,
        }
    )
    failed_transfer.status = "FAILED"
    failed_transfer.finished = failed_transfer.submitted
    database.session.add(failed_transfer)
    database.session.commit()

    run_command(cli_runner, app, cold, ["process-requests"])

    request = RequestMetadata.query.order_by(RequestMetadata.created_at.desc()).first()
    assert request.size == 1234
    assert request.num_failed_transfers == 1
