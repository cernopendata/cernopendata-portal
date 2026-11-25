import json
from unittest.mock import patch

import pytest
from invenio_files_rest.models import Location
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.api import RecordFilesWithIndex
from cernopendata.cold_storage.api import RecordAvailability
from cernopendata.cold_storage.models import RequestMetadata, RequestStatus
from cernopendata.modules.fixtures.cli import create_record


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

                request.status = RequestStatus.COMPLETED
                database.session.commit()

            else:
                assert not signal_mock.send.called
                assert RequestMetadata.query.count() == requests_count


@pytest.mark.parametrize(
    "recid, files, expected_body",
    [
        (
            "2201",
            [
                {
                    "checksum": "adler32:9719fd6a",
                    "size": 1053,
                    "uri": "root://foo/online.txt",
                }
            ],
            "All files are already available",
        ),
        ("2202", [], "No files found to stage"),
    ],
)
def test_stage_rejected_without_cold_files(
    app, client, database, recid, files, expected_body
):
    if not Location.query.filter_by(name="local").first():
        database.session.add(Location(name="local", uri="var/data", default=True))
    record = create_record(
        {
            "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
                "records/record-v1.0.0.json"
            ),
            "recid": recid,
            "date_published": "2024",
            "experiment": ["ALICE"],
            "publisher": "CERN Open Data Portal",
            "title": f"Record {recid}",
            "type": {"primary": "Dataset", "secondary": ["Derived"]},
            "files": files,
            "distribution": {
                "size": sum(record_file["size"] for record_file in files),
                "number_files": len(files),
            },
        },
        False,
    )
    record.commit()
    database.session.commit()
    requests_count = RequestMetadata.query.count()
    with patch("cernopendata.modules.records.utils.RecordIndexer"):
        with patch("cernopendata.modules.records.utils.record_stage") as signal_mock:
            result = client.post(
                f"/record/{recid}/stage",
                data=json.dumps({}),
                content_type="application/json",
            )

            assert result.status_code == 400
            assert expected_body in result.get_json()["error"]
            assert not signal_mock.send.called
            assert RequestMetadata.query.count() == requests_count

    pid = PersistentIdentifier.get("recid", recid)
    stored_record = RecordFilesWithIndex.get_record(pid.object_uuid)
    assert stored_record["availability"] == RecordAvailability.ONLINE.value
