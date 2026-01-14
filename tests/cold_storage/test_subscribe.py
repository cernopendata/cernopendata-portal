import json

import pytest

from cernopendata.cold_storage.api import Request
from cernopendata.cold_storage.models import RequestMetadata


@pytest.fixture()
def transfer(staged_record, database):
    request = Request.create(
        record_id=staged_record["record_id"],
        subscribers=["initial@example.com"],
        availability=staged_record["_availability_details"],
        distribution=staged_record["distribution"],
    )
    database.session.commit()
    return request


@pytest.mark.parametrize(
    "email, expected_status, expected_msg",
    [
        ("new-user@test.com", 200, "subscribed successfully"),
        ("not-an-email", 400, "is not a valid email address"),
        ("initial@example.com", 403, "is already subscribed"),
        ("", 400, "Missing email"),
    ],
)
def test_subscribe_endpoint(
    client, staged_record, transfer, email, expected_status, expected_msg
):
    payload = {"transfer_id": transfer.id, "email": email}
    recid = staged_record["recid"]
    result = client.post(
        f"/record/{recid}/subscribe",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert result.status_code == expected_status
    assert expected_msg in result.data.decode()

    if expected_status == 200:
        request = RequestMetadata.query.filter_by(
            id=transfer.id, record_id=transfer.record_id
        ).one()
        assert email in request.subscribers


def test_subscribe(app, database, staged_record):
    """Tests a subscription to a transfer"""
    record_id = staged_record["record_id"]
    request = Request.create(record_id)
    database.session.add(request)
    database.session.commit()

    # test a successful subscription
    subscriber = "new@domain.com"
    assert Request.subscribe(request.id, subscriber) is True
    request_md = RequestMetadata.query.filter_by(id=request.id).first()
    assert subscriber in request_md.subscribers

    # test trying to subscribe when already subscribed
    assert Request.subscribe(request.id, subscriber) is False
    request_md = RequestMetadata.query.filter_by(id=request.id).first()
    assert subscriber in request_md.subscribers
    assert len(request_md.subscribers) == 1


def test_send_email(app, database, smtp_server, staged_record):
    """Tests sending an email"""
    record_id = staged_record["record_id"]
    request = Request.create(record_id)
    database.session.add(request)
    database.session.commit()

    emails = ["my-email@test.ch"]
    Request.send_email(request, emails)
    assert len(smtp_server.inbox) == 1
    captured_email = smtp_server.inbox[0]
    assert captured_email["from"] == "opendata-noreply@cern.ch"
    assert captured_email["to"] == emails
    assert f"Transfer {request.id} Completed".encode() in captured_email["data"]
    assert (
        f"Your transfer with ID {request.id} has been completed successfully".encode()
        in captured_email["data"]
    )
