from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases import views
from .conftest import _raises


@patch("cernopendata.modules.releases.views._get_release")
def test_add_records_json_source(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release._metadata.num_records = 1
    mock_get_release.return_value = mock_release

    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json", "records": [{"recid": 1, "title": "Rec"}]},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["num_records"] == 1
    mock_release.add_records.assert_called_once()
    appended = mock_release.add_records.call_args[0][0]
    assert appended == [{"recid": 1, "title": "Rec"}]


@patch("cernopendata.modules.releases.views._get_release")
def test_add_records_json_source_single_dict_wrapped_in_list(
    mock_get_release, logged_in_client
):
    mock_release = MagicMock()
    mock_release._metadata.num_records = 1
    mock_get_release.return_value = mock_release

    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json", "records": {"recid": 1, "title": "Rec"}},
    )

    assert response.status_code == 200
    records = response.get_json()["records"]
    assert records == [{"recid": 1, "title": "Rec"}]
    appended = mock_release.add_records.call_args[0][0]
    assert appended == [{"recid": 1, "title": "Rec"}]


def test_add_records_missing_body(logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_json_source_missing_records_key(
    mock_get_release, logged_in_client
):
    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json"},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_url_source_missing_url(mock_get_release, logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url"},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_url_fetch_failure(mock_get_release, logged_in_client, monkeypatch):
    monkeypatch.setattr(
        views.requests, "get", _raises(views.requests.RequestException("refused"))
    )

    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url", "url": "http://example.com/recs.json"},
    )

    assert response.status_code == 400
    assert "Could not reach the URL" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_add_records_url_source_list_payload(
    mock_get_release, logged_in_client, monkeypatch
):
    mock_release = MagicMock()
    mock_release._metadata.num_records = 2
    mock_get_release.return_value = mock_release

    monkeypatch.setattr(
        views.requests,
        "get",
        lambda url, **k: MagicMock(
            json=lambda: [{"recid": 1}, {"recid": 2}],
            raise_for_status=lambda: None,
        ),
    )

    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url", "url": "http://example.com/recs.json"},
    )

    assert response.status_code == 200
    records = response.get_json()["records"]
    assert records == [{"recid": 1}, {"recid": 2}]


@patch("cernopendata.modules.releases.views._get_release")
def test_add_records_url_source_metadata_wrapper(
    mock_get_release, logged_in_client, monkeypatch
):
    mock_release = MagicMock()
    mock_release._metadata.num_records = 1
    mock_get_release.return_value = mock_release

    monkeypatch.setattr(
        views.requests,
        "get",
        lambda url, **k: MagicMock(
            json=lambda: {
                "metadata": {
                    "recid": 42,
                    "title": "Rec",
                    "_files": [{"key": "f.root"}],
                    "_bucket": "abc",
                    "bucket": "def",
                    "_file_indices": [],
                }
            },
            raise_for_status=lambda: None,
        ),
    )

    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url", "url": "http://example.com/rec.json"},
    )

    assert response.status_code == 200
    records = response.get_json()["records"]
    assert len(records) == 1
    assert records[0]["recid"] == 42
    assert records[0]["title"] == "Rec"
    for stripped in ("_files", "_bucket", "bucket", "_file_indices"):
        assert stripped not in records[0]


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_rejects_non_list_payload(mock_get_release, logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json", "records": "not a list"},
    )
    assert response.status_code == 400
