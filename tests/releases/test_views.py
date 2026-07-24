import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from flask import abort

from cernopendata.modules.releases import views
from cernopendata.modules.releases.views import _normalise_payload, _split_payload


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
        lambda *a, **k: (_ for _ in ()).throw(
            views.requests.RequestException("refused")
        ),
    )

    resp = logged_in_client.post(
        "/releases/cms/1/add_documents",
        json={"source": "urls", "urls": ["http://example.com/doc.json"]},
    )

    assert resp.status_code == 400
    assert "Could not reach the URL" in resp.get_json()["error"]


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
def test_add_records_json_source(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release._metadata.num_records = 1
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json", "records": [{"recid": 1, "title": "Rec"}]},
    )

    assert resp.status_code == 200
    data = resp.get_json()
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

    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json", "records": {"recid": 1, "title": "Rec"}},
    )

    assert resp.status_code == 200
    records = resp.get_json()["records"]
    assert records == [{"recid": 1, "title": "Rec"}]
    appended = mock_release.add_records.call_args[0][0]
    assert appended == [{"recid": 1, "title": "Rec"}]


def test_add_records_missing_body(logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        data="not json",
        content_type="text/plain",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_json_source_missing_records_key(
    mock_get_release, logged_in_client
):
    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json"},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_url_source_missing_url(mock_get_release, logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url"},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_url_fetch_failure(mock_get_release, logged_in_client, monkeypatch):
    monkeypatch.setattr(
        views.requests,
        "get",
        lambda *a, **k: (_ for _ in ()).throw(
            views.requests.RequestException("refused")
        ),
    )

    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url", "url": "http://example.com/recs.json"},
    )

    assert resp.status_code == 400
    assert "Could not reach the URL" in resp.get_json()["error"]


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

    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url", "url": "http://example.com/recs.json"},
    )

    assert resp.status_code == 200
    records = resp.get_json()["records"]
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

    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "url", "url": "http://example.com/rec.json"},
    )

    assert resp.status_code == 200
    records = resp.get_json()["records"]
    assert len(records) == 1
    assert records[0]["recid"] == 42
    assert records[0]["title"] == "Rec"
    for stripped in ("_files", "_bucket", "bucket", "_file_indices"):
        assert stripped not in records[0]


@patch("cernopendata.modules.releases.views._get_release", return_value=MagicMock())
def test_add_records_rejects_non_list_payload(mock_get_release, logged_in_client):
    resp = logged_in_client.post(
        "/releases/cms/1/add_records",
        json={"source": "json", "records": "not a list"},
    )
    assert resp.status_code == 400


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


@patch("cernopendata.modules.releases.views.stage_release")
@patch("cernopendata.modules.releases.views.db")
@patch("cernopendata.modules.releases.views._get_release")
def test_stage_release_dispatches_task(
    mock_get_release, mock_db, mock_stage_release, logged_in_client
):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post("/releases/cms/1/stage")

    assert resp.status_code == 302
    mock_stage_release.delay.assert_called_once()
    mock_release.stage.assert_not_called()


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


@pytest.mark.parametrize(
    "payload, expected_records, expected_documents",
    [
        ([], [], []),
        ([{"recid": 1, "files": []}], [{"recid": 1, "files": []}], []),
        ([{"slug": "x", "recid": 1}], [{"slug": "x", "recid": 1}], []),
        (
            [{"slug": "doc-1", "body": {"content": "hi", "format": "md"}}],
            [],
            [
                {
                    "slug": "doc-1",
                    "body": {"content": "hi", "format": "md"},
                    "_source_filename": "f.json",
                }
            ],
        ),
        (
            [{"title": "X", "body": {"content": "text", "format": "md"}}],
            [],
            [
                {
                    "title": "X",
                    "body": {"content": "text", "format": "md"},
                    "_source_filename": "f.json",
                }
            ],
        ),
        (
            {
                "records": [{"recid": 1, "files": []}],
                "documents": [
                    {"slug": "doc-1", "body": {"content": "hi", "format": "md"}}
                ],
            },
            [{"recid": 1, "files": []}],
            [
                {
                    "slug": "doc-1",
                    "body": {"content": "hi", "format": "md"},
                    "_source_filename": "f.json",
                }
            ],
        ),
        ({"records": [{"recid": 1, "files": []}]}, [{"recid": 1, "files": []}], []),
    ],
)
def test_split_payload(payload, expected_records, expected_documents):
    assert _split_payload(payload, "f.json") == (expected_records, expected_documents)


@patch("cernopendata.modules.releases.views.Release.create")
@patch("cernopendata.modules.releases.views.curator_experiments")
@patch("cernopendata.modules.releases.views.Release.validate_experiment")
def test_upload_file_creates_release_with_records_and_documents(
    mock_validate_exp, mock_curator_exps, mock_create, logged_in_client
):
    mock_validate_exp.return_value = True
    mock_curator_exps.return_value = {"curator_experiments": ["cms"]}
    mock_create.return_value = MagicMock(_metadata=MagicMock(id=99))

    records = [{"recid": 1, "experiment": "CMS", "files": []}]
    docs = [{"slug": "test-document", "body": {"content": "# About", "format": "md"}}]
    payload = {
        "name": "CMS 2016 collision data",
        "description": "Primary datasets",
        "discussion_url": "https://example.com/discussion",
        "records": records,
        "documents": docs,
    }
    resp = logged_in_client.post(
        "/releases/cms",
        data={
            "source": "file",
            "file": (BytesIO(json.dumps(payload).encode()), "release-1.json"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    _, kwargs = mock_create.call_args
    assert kwargs.get("records") == records
    assert kwargs.get("documents")[0]["slug"] == "test-document"
    assert kwargs.get("documents")[0]["_source_filename"] == "release-1.json"
    assert kwargs.get("name") == "CMS 2016 collision data"
    assert kwargs.get("description") == "Primary datasets"
    assert kwargs.get("discussion_url") == "https://example.com/discussion"


@patch("cernopendata.modules.releases.views.Release.create")
@patch("cernopendata.modules.releases.views.curator_experiments")
@patch("cernopendata.modules.releases.views.Release.validate_experiment")
def test_upload_file_without_name_falls_back_to_filename(
    mock_validate_exp, mock_curator_exps, mock_create, logged_in_client
):
    mock_validate_exp.return_value = True
    mock_curator_exps.return_value = {"curator_experiments": ["cms"]}
    mock_create.return_value = MagicMock(_metadata=MagicMock(id=99))

    payload = {"records": [{"recid": 1, "experiment": "CMS", "files": []}]}
    resp = logged_in_client.post(
        "/releases/cms",
        data={
            "source": "file",
            "file": (BytesIO(json.dumps(payload).encode()), "release-1.json"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    _, kwargs = mock_create.call_args
    assert kwargs.get("name") == "release-1.json"


@patch("cernopendata.modules.releases.views._get_release")
def test_download_release_includes_records_and_documents(mock_get_release, client):
    records = [{"recid": 1, "experiment": "CMS"}]
    docs = [{"slug": "doc-1", "body": {"content": "hi", "format": "md"}}]
    metadata = MagicMock(
        description="Primary datasets",
        discussion_url="https://example.com/discussion",
        records=records,
        documents=docs,
    )
    metadata.name = "CMS 2016 collision data"
    mock_get_release.return_value = MagicMock(_metadata=metadata)

    resp = client.get("/releases/api/cms/1")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["name"] == "CMS 2016 collision data"
    assert body["description"] == "Primary datasets"
    assert body["discussion_url"] == "https://example.com/discussion"
    assert body["records"] == records
    assert body["documents"] == docs
    assert (
        resp.headers["Content-Disposition"]
        == "attachment; filename=CMS_2016_collision_data.json"
    )


@pytest.fixture
def images_path(app, tmp_path, monkeypatch):
    """Override CERNOPENDATA_IMAGES_PATH to a tmp dir for the duration of a test."""
    monkeypatch.setitem(app.config, "CERNOPENDATA_IMAGES_PATH", str(tmp_path))
    return tmp_path


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_success(mock_get_release, logged_in_client, images_path):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"fake-png-bytes"), "Figure1.PNG"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["images"] == [
        {
            "filename": "figure1.png",
            "parent_slug": "alice-doc",
            "url": "/static/upload/1/alice-doc/figure1.png",
        }
    ]
    written = images_path / "1" / "alice-doc" / "figure1.png"
    assert written.is_file()
    assert written.read_bytes() == b"fake-png-bytes"


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_multiple_files(mock_get_release, logged_in_client, images_path):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": [
                (BytesIO(b"a"), "a.png"),
                (BytesIO(b"b"), "b.jpg"),
            ],
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    filenames = [img["filename"] for img in resp.get_json()["images"]]
    assert filenames == ["a.png", "b.jpg"]
    assert (images_path / "1" / "alice-doc" / "a.png").is_file()
    assert (images_path / "1" / "alice-doc" / "b.jpg").is_file()


def test_upload_image_missing_parent_slug(logged_in_client, images_path):
    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={"images": (BytesIO(b"x"), "x.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_upload_image_no_files(logged_in_client, images_path):
    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={"parent_slug": "alice-doc"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_unknown_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "missing-doc",
            "images": (BytesIO(b"x"), "x.png"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_unsupported_extension(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"x"), "evil.exe"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_oversized_file(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    big_payload = b"0" * (views.MAX_IMAGE_SIZE + 1)
    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(big_payload), "big.png"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert not (images_path / "1" / "alice-doc" / "big.png").exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_path_traversal_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "../escape"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "../escape",
            "images": (BytesIO(b"x"), "x.png"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_collision_with_existing_file(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    (images_path / "1" / "alice-doc").mkdir(parents=True)
    (images_path / "1" / "alice-doc" / "figure1.png").write_bytes(b"original")

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"replacement"), "Figure1.PNG"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 409
    assert "already exists" in resp.get_json()["error"]
    assert (images_path / "1" / "alice-doc" / "figure1.png").read_bytes() == b"original"


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_collision_within_batch(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": [
                (BytesIO(b"first"), "Figure1.png"),
                (BytesIO(b"second"), "figure1.PNG"),
            ],
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 409
    assert (images_path / "1" / "alice-doc" / "figure1.png").read_bytes() == b"first"


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_returns_images_on_disk(
    mock_get_release, logged_in_client, images_path
):
    (images_path / "1" / "alice-doc").mkdir(parents=True)
    (images_path / "1" / "alice-doc" / "a.png").write_bytes(b"a")
    (images_path / "1" / "alice-doc" / "b.jpg").write_bytes(b"b")
    (images_path / "1" / "alice-doc" / "ignored.txt").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(
        documents=[{"slug": "alice-doc"}, {"slug": "no-images-doc"}]
    )

    resp = logged_in_client.get("/releases/cms/1/images")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["images"] == [
        {
            "filename": "a.png",
            "parent_slug": "alice-doc",
            "url": "/static/upload/1/alice-doc/a.png",
        },
        {
            "filename": "b.jpg",
            "parent_slug": "alice-doc",
            "url": "/static/upload/1/alice-doc/b.jpg",
        },
    ]


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_skips_documents_without_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(
        documents=[{"title": "no slug"}, {"slug": ""}]
    )

    resp = logged_in_client.get("/releases/cms/1/images")
    assert resp.status_code == 200
    assert resp.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_when_no_directory_exists(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.get("/releases/cms/1/images")
    assert resp.status_code == 200
    assert resp.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_success_and_removes_empty_dir(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "a.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
    assert not (slug_dir / "a.png").exists()
    assert not slug_dir.exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_keeps_non_empty_dir(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "a.png").write_bytes(b"a")
    (slug_dir / "b.png").write_bytes(b"b")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert resp.status_code == 200
    assert (slug_dir / "b.png").exists()
    assert slug_dir.exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_unknown_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.delete("/releases/cms/1/images/other-doc/a.png")
    assert resp.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_file_not_found(mock_get_release, logged_in_client, images_path):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.delete("/releases/cms/1/images/alice-doc/missing.png")
    assert resp.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_success(mock_get_release, logged_in_client, images_path):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "New.PNG"},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["image"] == {
        "filename": "new.png",
        "parent_slug": "alice-doc",
        "url": "/static/upload/1/alice-doc/new.png",
    }
    assert not (slug_dir / "old.png").exists()
    assert (slug_dir / "new.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_same_name_is_noop(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "same.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/same.png",
        json={"filename": "same.png"},
    )

    assert resp.status_code == 200
    assert (slug_dir / "same.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_conflict_when_target_exists(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "old.png").write_bytes(b"a")
    (slug_dir / "new.png").write_bytes(b"b")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.png"},
    )

    assert resp.status_code == 409
    assert (slug_dir / "old.png").is_file()
    assert (slug_dir / "new.png").read_bytes() == b"b"


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_source_not_found(mock_get_release, logged_in_client, images_path):
    (images_path / "1" / "alice-doc").mkdir(parents=True)
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/missing.png",
        json={"filename": "new.png"},
    )
    assert resp.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_missing_new_filename(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_unsupported_extension(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.exe"},
    )
    assert resp.status_code == 400
    assert (slug_dir / "old.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_unknown_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/other-doc/old.png",
        json={"filename": "new.png"},
    )
    assert resp.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_filename_that_sanitizes_to_empty(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"x"), ".."),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_target_path_escape(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(views, "secure_filename", lambda _: "../escape.png")

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"x"), "anything.png"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert not (images_path / "escape.png").exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_skips_doc_slug_path_traversal(
    mock_get_release, logged_in_client, images_path
):
    sibling = images_path.parent / "sibling-leak"
    sibling.mkdir(exist_ok=True)
    (sibling / "secret.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "../sibling-leak"}])

    resp = logged_in_client.get("/releases/cms/1/images")

    assert resp.status_code == 200
    assert resp.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rejects_parent_slug_path_traversal(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": ".."}])

    resp = logged_in_client.delete("/releases/cms/1/images/../file.png")
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rejects_filename_that_sanitizes_to_empty(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.delete("/releases/cms/1/images/alice-doc/..")
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rejects_target_path_escape(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    (images_path / "1" / "alice-doc").mkdir(parents=True)
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(views, "secure_filename", lambda _: "../escape.png")

    resp = logged_in_client.delete("/releases/cms/1/images/alice-doc/anything.png")
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_parent_slug_path_traversal(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": ".."}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/../old.png",
        json={"filename": "new.png"},
    )
    assert resp.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_target_path_escape(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(views, "secure_filename", lambda _: "../escape.png")

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.png"},
    )
    assert resp.status_code == 400
    assert (slug_dir / "old.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_new_filename_that_sanitizes_to_empty(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": ".."},
    )
    assert resp.status_code == 400
    assert (slug_dir / "old.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_mkdir_oserror_returns_500(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(
        "cernopendata.modules.releases.views.Path.mkdir",
        lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")),
    )

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"img"), "photo.png"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 500
    assert "Could not prepare upload directory" in resp.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_save_oserror_returns_500(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.parent.mkdir()
    slug_dir.mkdir(mode=0o444)  # read-only: file.save() will raise OSError
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    resp = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"img"), "photo.png"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 500
    assert "Could not save image" in resp.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_iterdir_oserror_skips_directory(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "ok.png").write_bytes(b"x")

    mock_get_release.return_value = MagicMock(
        documents=[{"slug": "alice-doc"}, {"slug": "other-doc"}]
    )

    resp = logged_in_client.get("/releases/cms/1/images")

    assert resp.status_code == 200
    images = resp.get_json()["images"]
    assert len(images) == 1
    assert images[0]["filename"] == "ok.png"


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_unlink_oserror_returns_500(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "a.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        type(slug_dir / "a.png"),
        "unlink",
        lambda *a, **k: (_ for _ in ()).throw(OSError("locked")),
    )

    resp = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert resp.status_code == 500
    assert "Could not delete image" in resp.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_oserror_returns_500(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "old.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        type(slug_dir / "old.png"),
        "rename",
        lambda *a, **k: (_ for _ in ()).throw(OSError("locked")),
    )

    resp = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.png"},
    )

    assert resp.status_code == 500
    assert "Could not rename image" in resp.get_json()["error"]


def test_preview_requires_json(client, logged_in_client):
    response = client.post(
        "/releases/preview_record",
        data="not json",
        content_type="application/json",
    )

    assert response.status_code == 400


def test_preview_requires_dict_payload(client, logged_in_client):
    response = client.post(
        "/releases/preview_record",
        data=json.dumps(["not", "a", "dict"]),
        content_type="application/json",
    )

    assert response.status_code == 400


def test_preview_renders_record(client, logged_in_client):
    payload = {
        "recid": 123,
        "title": "My test record",
        "doi": "10.1234/test",
    }

    response = client.post(
        "/releases/preview_record",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "html" in data

    html = data["html"]

    assert "My test record" in html
    assert "10.1234/test" in html


def test_preview_document_requires_json(client, logged_in_client):
    response = client.post(
        "/releases/preview_document",
        data="not json",
        content_type="application/json",
    )

    assert response.status_code == 400


def test_preview_document_requires_dict_payload(client, logged_in_client):
    response = client.post(
        "/releases/preview_document",
        data=json.dumps(["not", "a", "dict"]),
        content_type="application/json",
    )

    assert response.status_code == 400


def test_preview_document_renders_doc(client, logged_in_client):
    payload = {
        "slug": "my-test-doc",
        "title": "My test document",
        "body": {"format": "md", "content": "# Hello"},
    }

    response = client.post(
        "/releases/preview_document",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "html" in data

    html = data["html"]

    assert "My test document" in html
    assert "Hello" in html


def test_fetch_json_http_error_raises_url_fetch_error(monkeypatch):
    response = MagicMock(status_code=404, reason="Not Found")
    error = views.requests.HTTPError(response=response)

    def raise_for_status():
        raise error

    monkeypatch.setattr(
        views.requests,
        "get",
        lambda *a, **k: MagicMock(raise_for_status=raise_for_status),
    )

    with pytest.raises(views.URLFetchError) as exc_info:
        views._fetch_json("http://example.com/file.json")
    assert "404" in str(exc_info.value)
    assert "Not Found" in str(exc_info.value)


def test_fetch_json_invalid_json_raises_url_fetch_error(monkeypatch):
    def json_raises():
        raise ValueError("not json")

    monkeypatch.setattr(
        views.requests,
        "get",
        lambda *a, **k: MagicMock(
            raise_for_status=lambda: None,
            json=json_raises,
        ),
    )

    with pytest.raises(views.URLFetchError) as exc_info:
        views._fetch_json("http://example.com/file.json")
    assert "valid JSON" in str(exc_info.value)


@patch(
    "cernopendata.modules.releases.views.curator_experiments",
    return_value={"curator_experiments": ["cms"]},
)
@patch(
    "cernopendata.modules.releases.views.Release.validate_experiment",
    return_value=True,
)
def test_release_upload_url_source_missing_url(
    mock_validate, mock_curator, logged_in_client
):
    response = logged_in_client.post("/releases/cms", data={"source": "url"})
    assert response.status_code == 400


@patch(
    "cernopendata.modules.releases.views.curator_experiments",
    return_value={"curator_experiments": ["cms"]},
)
@patch(
    "cernopendata.modules.releases.views.Release.validate_experiment",
    return_value=True,
)
def test_release_upload_url_source_fetch_failure(
    mock_validate, mock_curator, logged_in_client, monkeypatch
):
    monkeypatch.setattr(
        views.requests,
        "get",
        lambda *a, **k: (_ for _ in ()).throw(
            views.requests.RequestException("refused")
        ),
    )

    response = logged_in_client.post(
        "/releases/cms",
        data={"source": "url", "url": "http://example.com/file.json"},
    )

    assert response.status_code == 400
    assert "Could not reach the URL" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_iterdir_raising_oserror_logs_and_skips(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "ok.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        "cernopendata.modules.releases.views.Path.iterdir",
        lambda *a, **k: (_ for _ in ()).throw(OSError("permission denied")),
    )

    response = logged_in_client.get("/releases/cms/1/images")

    assert response.status_code == 200
    assert response.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_unlink_file_not_found_returns_404(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "a.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        type(slug_dir / "a.png"),
        "unlink",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("gone")),
    )

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert response.status_code == 404
    assert "Image not found" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rmdir_oserror_still_returns_ok(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "1" / "alice-doc"
    slug_dir.mkdir(parents=True)
    (slug_dir / "a.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        type(slug_dir),
        "rmdir",
        lambda *a, **k: (_ for _ in ()).throw(OSError("not empty")),
    )

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert not (slug_dir / "a.png").exists()


@patch("cernopendata.modules.releases.views.db")
@patch("cernopendata.modules.releases.views._get_release")
def test_generate_doi_endpoint_returns_records_and_errors(
    mock_get_release, mock_db, logged_in_client
):
    mock_release = MagicMock()
    mock_release.generate_doi.return_value = [{"recid": 1, "error": "bad field"}]
    mock_release.records = [{"recid": 1, "doi": ""}]
    mock_get_release.return_value = mock_release

    response = logged_in_client.post(
        "/releases/cms/1/generate_doi", json={"recids": [1]}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["records"] == [{"recid": 1, "doi": ""}]
    assert data["errors"] == [{"recid": 1, "error": "bad field"}]
    mock_release.generate_doi.assert_called_once_with([1])
    mock_db.session.commit.assert_called_once()


def test_generate_doi_endpoint_rejects_non_staged(logged_in_client):
    with patch(
        "cernopendata.modules.releases.views._get_release",
        side_effect=lambda *_args, **_kwargs: abort(409),
    ):
        response = logged_in_client.post("/releases/cms/1/generate_doi")

    assert response.status_code == 409


@patch("cernopendata.modules.releases.views.publish_release")
@patch("cernopendata.modules.releases.views.db")
@patch("cernopendata.modules.releases.views._get_release")
def test_publish_dispatches_task(
    mock_get_release, mock_db, mock_publish_release, logged_in_client
):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post("/releases/cms/1/publish")

    assert resp.status_code == 302
    mock_publish_release.delay.assert_called_once()
    mock_release.publish.assert_not_called()


@patch("cernopendata.modules.releases.views.rollback_release")
@patch("cernopendata.modules.releases.views.db")
@patch("cernopendata.modules.releases.views._get_release")
def test_rollback_dispatches_task(
    mock_get_release, mock_db, mock_rollback_release, logged_in_client
):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    resp = logged_in_client.post("/releases/cms/1/rollback")

    assert resp.status_code == 302
    mock_rollback_release.delay.assert_called_once()
    mock_release.rollback.assert_not_called()
