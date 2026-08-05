import json
import logging

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

    emails = ["my-email@test.ch", "another-email@test.ch"]
    Request.send_email(request, emails)
    assert len(smtp_server.inbox) == len(emails)
    for email, captured_email in zip(emails, smtp_server.inbox):
        assert captured_email["from"] == "opendata-noreply@cern.ch"
        assert captured_email["to"] == [email]
        assert f"Transfer {request.id} Completed".encode() in captured_email["data"]
        assert (
            f"Your transfer with ID {request.id} has been completed successfully".encode()
            in captured_email["data"]
        )


def test_mark_as_completed_notifies_each_subscriber(
    app, database, smtp_server, staged_record
):
    """Tests that completing a request sends one email per subscriber"""
    record_id = staged_record["record_id"]
    subscribers = ["first@test.ch", "second@test.ch", "third@test.ch"]
    request = Request.create(record_id, subscribers=subscribers)
    database.session.add(request)
    database.session.commit()

    assert Request.mark_as_completed(request) is True

    request_md = RequestMetadata.query.filter_by(id=request.id).first()
    assert request_md.status == "completed"
    assert request_md.completed_at is not None

    assert len(smtp_server.inbox) == len(subscribers)
    recipients = [captured_email["to"] for captured_email in smtp_server.inbox]
    assert recipients == [[subscriber] for subscriber in subscribers]


def test_send_email_continues_after_a_failure(
    app, database, smtp_server, staged_record, monkeypatch, caplog
):
    """Tests that a failing recipient does not stop the remaining ones"""
    record_id = staged_record["record_id"]
    request = Request.create(record_id)
    database.session.add(request)
    database.session.commit()

    failing_email = "broken@test.ch"
    mail_extension = app.extensions["mail"]
    original_send = mail_extension.send

    def send_rejecting_one_recipient(message):
        if failing_email in message.recipients:
            raise RuntimeError("relay refused")
        return original_send(message)

    monkeypatch.setattr(mail_extension, "send", send_rejecting_one_recipient)

    emails = ["first@test.ch", failing_email, "third@test.ch"]
    with caplog.at_level(logging.ERROR):
        Request.send_email(request, emails)

    recipients = [captured_email["to"] for captured_email in smtp_server.inbox]
    assert recipients == [["first@test.ch"], ["third@test.ch"]]
    assert f"Failed to send email to {failing_email}: relay refused" in caplog.text
