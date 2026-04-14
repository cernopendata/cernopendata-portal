import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from cernopendata.modules.releases import views
from cernopendata.modules.releases.api import Release
from cernopendata.modules.releases.models import ReleaseStatus
from cernopendata.modules.releases.views import _detect_payload_type


@pytest.fixture
def logged_in_client(client):
    """Client with a mock authenticated user bypassing flask_login."""
    mock_user = MagicMock(
        is_authenticated=True, is_active=True, is_anonymous=False, get_id=lambda: "1"
    )
    mock_user.id = 1
    mock_remote_account = MagicMock()
    mock_remote_account.extra_data = {"cern_roles": []}
    with patch("flask_login.utils._get_user", return_value=mock_user), patch(
        "invenio_communities.ext.load_community_needs"
    ), patch(
        "invenio_oauthclient.models.RemoteAccount.get",
        return_value=mock_remote_account,
    ):
        yield client


def test_list_releases(client):
    # Patch current_user to be authenticated
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    with patch("cernopendata.modules.releases.views.current_user", mock_user), patch(
        "cernopendata.modules.releases.views.Release.validate_experiment",
        return_value=True,
    ), patch(
        "cernopendata.modules.releases.views.curator_experiments",
        return_value={"curator_experiments": ["cms"]},
    ), patch(
        "cernopendata.modules.releases.views.Release.list_releases", return_value=[]
    ):

        res = client.get("/releases/api/list/cms")

    assert res.status_code == 302


def test_invalid_experiment(client):
    resp = client.get("/releases/list/batlas")
    assert resp.status_code in (403, 404)


def test_upload_url(client, monkeypatch):
    class FakeResp:
        def json(self):
            return {"x": 1}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(views.requests, "get", lambda *a, **k: FakeResp())

    resp = client.post(
        "/releases/cms",
        data={"source": "url", "url": "http://example.com/file.json"},
    )

    assert resp.status_code == 302


@patch("cernopendata.modules.releases.views._get_release")
def test_add_documents_json_source(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release._metadata.num_docs = 1
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "json", "documents": [{"slug": "my-doc", "title": "My Doc"}]},
    )

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["num_docs"] == 1
    mock_release.add_documents.assert_called_once()


def test_add_documents_missing_body(logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        data="not json",
        content_type="text/plain",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_json_source_empty_list(mock_get_release, logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "json", "documents": []},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_source_no_urls(mock_get_release, logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": []},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_fetch_failure(
    mock_get_release, logged_in_client, monkeypatch
):
    monkeypatch.setattr(
        views.requests,
        "get",
        lambda *a, **k: (_ for _ in ()).throw(Exception("refused")),
    )

    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/doc.json"]},
    )

    assert resp.status_code == 400
    assert "Failed to fetch" in resp.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_urls_non_json_rejected(mock_get_release, logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/readme.md"]},
    )

    assert resp.status_code == 400
    assert "must point to a .json file" in resp.get_json()["error"]


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

    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/doc.json"]},
    )

    assert resp.status_code == 200
    docs = resp.get_json()["documents"]
    assert docs[0]["body"]["content"] == "# Inlined body"
    assert docs[0].get("_source_filename") == "doc.json"


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_documents_json_source_filename_pointer_rejected(
    mock_get_release, logged_in_client
):
    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={
            "source": "json",
            "documents": [
                {"slug": "my-doc", "body": {"content": "my-doc.md", "format": "md"}}
            ],
        },
    )

    assert resp.status_code == 400
    assert "filename pointer" in resp.get_json()["error"]


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

    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/my-doc.json"]},
    )

    assert resp.status_code == 400
    assert "filename pointer" in resp.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_update_document_success(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    resp = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        json={"document": {"slug": "my-doc", "title": "Updated"}},
    )

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
    mock_release.update_document.assert_called_once()


def test_update_document_missing_document(logged_in_client):
    resp = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        json={"title": "No document key"},
    )
    assert resp.status_code == 400


def test_update_document_missing_body(logged_in_client):
    resp = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        data="not json",
        content_type="text/plain",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_stage_release_calls_stage(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post("/releases/cms/1/stage")

    assert resp.status_code == 302
    mock_release.stage.assert_called_once()


@patch("cernopendata.modules.releases.views._get_release")
def test_stage_release_swallows_exception(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release.stage.side_effect = RuntimeError("boom")
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post("/releases/cms/1/stage")

    assert resp.status_code == 302


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_update_document_missing_document_data(mock_get_release, logged_in_client):
    resp = logged_in_client.put(
        "/releases/cms/1/documents/my-doc",
        json={},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_update_document_slug_not_found(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release.update_document.side_effect = ValueError(
        "Document with slug 'missing' not found"
    )
    mock_get_release.return_value = mock_release

    resp = logged_in_client.put(
        "/releases/cms/1/documents/missing",
        json={"document": {"slug": "missing", "title": "X"}},
    )

    assert resp.status_code == 404
    assert "not found" in resp.get_json()["error"]


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


@patch("cernopendata.modules.releases.views.Release.create")
@patch("cernopendata.modules.releases.views.curator_experiments")
@patch("cernopendata.modules.releases.views.Release.validate_experiment")
def test_upload_file_documents_payload_routes_to_create_documents(
    mock_validate_exp, mock_curator_exps, mock_create, logged_in_client
):
    mock_validate_exp.return_value = True
    mock_curator_exps.return_value = {"curator_experiments": ["cms"]}
    mock_create.return_value = MagicMock(_metadata=MagicMock(id=99))

    doc = {"slug": "test-document", "body": {"content": "# About", "format": "md"}}
    resp = logged_in_client.post(
        "/releases/cms",
        data={
            "source": "file",
            "file": (BytesIO(json.dumps(doc).encode()), "test-document.json"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    _, kwargs = mock_create.call_args
    assert kwargs.get("documents")[0]["slug"] == "test-document"
    assert kwargs.get("documents")[0]["_source_filename"] == "test-document.json"
    assert "records" not in kwargs


@patch("cernopendata.modules.releases.views.Release.create")
@patch("cernopendata.modules.releases.views.curator_experiments")
@patch("cernopendata.modules.releases.views.Release.validate_experiment")
def test_upload_file_records_payload_routes_to_create_records(
    mock_validate_exp, mock_curator_exps, mock_create, logged_in_client
):
    mock_validate_exp.return_value = True
    mock_curator_exps.return_value = {"curator_experiments": ["cms"]}
    mock_create.return_value = MagicMock(_metadata=MagicMock(id=99))

    records = [{"recid": 1, "experiment": "CMS", "files": []}]
    resp = logged_in_client.post(
        "/releases/cms",
        data={
            "source": "file",
            "file": (BytesIO(json.dumps(records).encode()), "cms-release.json"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    _, kwargs = mock_create.call_args
    assert kwargs.get("records") == records
    assert "documents" not in kwargs
