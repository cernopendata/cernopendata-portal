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
