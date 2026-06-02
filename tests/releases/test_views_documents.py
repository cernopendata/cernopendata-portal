from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases import views
from cernopendata.modules.releases.views import _detect_payload_type, _normalise_payload
from .conftest import _raises


@patch("cernopendata.modules.releases.views._get_release")
def test_add_documents_json_source(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release._metadata.num_docs = 1
    mock_get_release.return_value = mock_release

    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "json", "documents": [{"slug": "my-doc", "title": "My Doc"}]},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["num_docs"] == 1
    mock_release.add_documents.assert_called_once()


def test_add_documents_missing_body(logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_json_source_empty_list(mock_get_release, logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "json", "documents": []},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_source_no_urls(mock_get_release, logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": []},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_fetch_failure(
    mock_get_release, logged_in_client, monkeypatch
):
    monkeypatch.setattr(
        views.requests, "get", _raises(views.requests.RequestException("refused"))
    )

    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/doc.json"]},
    )

    assert response.status_code == 400
    assert "Could not reach the URL" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_non_json_rejected(mock_get_release, logged_in_client):
    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/readme.md"]},
    )

    assert response.status_code == 400
    assert "must point to a .json file" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_add_documents_urls_json_with_inlined_body(
    mock_get_release, logged_in_client, monkeypatch
):
    mock_release = MagicMock()
    mock_release._metadata.num_docs = 1
    mock_get_release.return_value = mock_release

    monkeypatch.setattr(
        views.requests,
        "get",
        lambda url, **k: MagicMock(
            json=lambda: {
                "slug": "doc-1",
                "title": "Doc",
                "body": {"content": "# Inlined body", "format": "md"},
            },
            raise_for_status=lambda: None,
        ),
    )

    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/doc.json"]},
    )

    assert response.status_code == 200
    docs = response.get_json()["documents"]
    assert docs[0]["body"]["content"] == "# Inlined body"
    assert docs[0].get("_source_filename") == "doc.json"


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_json_source_filename_pointer_rejected(
    mock_get_release, logged_in_client
):
    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={
            "source": "json",
            "documents": [
                {"slug": "my-doc", "body": {"content": "my-doc.md", "format": "md"}}
            ],
        },
    )

    assert response.status_code == 400
    assert "filename pointer" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_filename_pointer_rejected(
    mock_get_release, logged_in_client, monkeypatch
):
    monkeypatch.setattr(
        views.requests,
        "get",
        lambda url, **k: MagicMock(
            json=lambda: {
                "slug": "my-doc",
                "body": {"content": "my-doc.md", "format": "md"},
            },
            raise_for_status=lambda: None,
        ),
    )

    response = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/my-doc.json"]},
    )

    assert response.status_code == 400
    assert "filename pointer" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_update_document_success(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    response = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        json={"document": {"slug": "my-doc", "title": "Updated"}},
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    mock_release.update_document.assert_called_once()


def test_update_document_missing_document(logged_in_client):
    response = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        json={"title": "No document key"},
    )
    assert response.status_code == 400


def test_update_document_missing_body(logged_in_client):
    response = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_update_document_missing_document_data(mock_get_release, logged_in_client):
    response = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        json={},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_update_document_slug_not_found(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release.update_document.side_effect = ValueError(
        "Document with slug 'missing' not found"
    )
    mock_get_release.return_value = mock_release

    response = logged_in_client.put(
        "/releases/cms/1/documents/missing",
        json={"document": {"slug": "missing", "title": "X"}},
    )

    assert response.status_code == 404
    assert "not found" in response.get_json()["error"]


def test_detect_payload_kind_empty():
    assert _detect_payload_type([]) == "records"


def test_detect_payload_kind_record():
    assert (
        _detect_payload_type([{"recid": 1, "files": [], "experiment": "CMS"}])
        == "records"
    )


def test_detect_payload_kind_document_with_slug():
    assert (
        _detect_payload_type(
            [{"slug": "test-document", "body": {"content": "# Hi", "format": "md"}}]
        )
        == "documents"
    )


def test_detect_payload_kind_document_with_body_only():
    assert (
        _detect_payload_type(
            [{"title": "X", "body": {"content": "text", "format": "md"}}]
        )
        == "documents"
    )


def test_detect_payload_kind_slug_plus_recid_is_records():
    assert _detect_payload_type([{"slug": "x", "recid": 1}]) == "records"


def test_normalise_payload_list_passthrough():
    payload = [{"recid": 1}, {"recid": 2}]
    assert _normalise_payload(payload) == payload


def test_normalise_payload_dict_wraps_in_list():
    assert _normalise_payload({"recid": 1}) == [{"recid": 1}]


def test_normalise_payload_metadata_wrapper_unwraps_and_strips_internals():
    payload = {
        "metadata": {
            "recid": 1,
            "title": "Rec",
            "_files": [{"key": "f.root"}],
            "_bucket": "abc",
            "bucket": "def",
            "_file_indices": [],
        }
    }
    assert _normalise_payload(payload) == [{"recid": 1, "title": "Rec"}]
