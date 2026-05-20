import json


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
