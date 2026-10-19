import json
from unittest.mock import patch

import pytest

from cernopendata.cold_storage.models import RequestMetadata


@pytest.mark.parametrize(
    "payload, expected_status, expected_body",
    [
        ({"email": "valid@example.com"}, 200, "OK"),
        ({"email": "not-an-email"}, 400, "Invalid email address"),
        ({}, 200, "OK"),
    ],
)
def test_stage_endpoint(
    app, client, database, staged_record, payload, expected_status, expected_body
):
    recid = staged_record["recid"]
    requests_count = RequestMetadata.query.count()
    with patch("cernopendata.modules.records.utils.RecordIndexer"):
        with patch("cernopendata.modules.records.utils.record_stage") as signal_mock:
            result = client.post(
                f"/record/{recid}/stage",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert result.status_code == expected_status
            assert expected_body in result.data.decode()

            if expected_status == 200:
                assert signal_mock.send.called
                assert RequestMetadata.query.count() == requests_count + 1
                request = RequestMetadata.query.order_by(
                    RequestMetadata.created_at.desc()
                ).first()
                if payload.get("email"):
                    assert payload["email"] in request.subscribers
                else:
                    assert request.subscribers == []

                signal_mock.reset_mock()
                duplicate_result = app.test_client().post(
                    f"/record/{recid}/stage",
                    data=json.dumps({"file": "file.txt"}),
                    content_type="application/json",
                )
                assert duplicate_result.status_code == 409
                assert duplicate_result.get_json()["transfer_id"] == request.id
                assert not signal_mock.send.called
                assert RequestMetadata.query.count() == requests_count + 1

                request.status = "completed"
                database.session.commit()

            else:
                assert not signal_mock.send.called
                assert RequestMetadata.query.count() == requests_count
