import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases import views


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

        response = client.get("/releases/api/list/cms")

    assert response.status_code == 302


def test_invalid_experiment(client):
    response = client.get("/releases/list/batlas")
    assert response.status_code in (403, 404)


def test_upload_url(client, monkeypatch):
    class FakeResp:
        def json(self):
            return {"x": 1}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(views.requests, "get", lambda *a, **k: FakeResp())

    response = client.post(
        "/releases/cms",
        data={"source": "url", "url": "http://example.com/file.json"},
    )

    assert response.status_code == 302


@patch("cernopendata.modules.releases.views._get_release")
def test_stage_release_calls_stage(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_get_release.return_value = mock_release

    response = logged_in_client.post("/releases/cms/1/stage")

    assert response.status_code == 302
    mock_release.stage.assert_called_once()


@patch("cernopendata.modules.releases.views._get_release")
def test_stage_release_swallows_exception(mock_get_release, logged_in_client):
    mock_release = MagicMock()
    mock_release.stage.side_effect = RuntimeError("boom")
    mock_get_release.return_value = mock_release

    response = logged_in_client.post("/releases/cms/1/stage")

    assert response.status_code == 302


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
    response = logged_in_client.post(
        "/releases/cms",
        data={
            "source": "file",
            "file": (BytesIO(json.dumps(doc).encode()), "test-document.json"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
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
    response = logged_in_client.post(
        "/releases/cms",
        data={
            "source": "file",
            "file": (BytesIO(json.dumps(records).encode()), "cms-release.json"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    _, kwargs = mock_create.call_args
    assert kwargs.get("records") == records
    assert "documents" not in kwargs


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
