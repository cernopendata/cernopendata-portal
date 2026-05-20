from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases import views


@pytest.fixture
def images_path(app, tmp_path, monkeypatch):
    """Override CERNOPENDATA_IMAGES_PATH to a tmp dir for the duration of a test."""
    monkeypatch.setitem(app.config, "CERNOPENDATA_IMAGES_PATH", str(tmp_path))
    return tmp_path


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_success(mock_get_release, logged_in_client, images_path):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"fake-png-bytes"), "Figure1.PNG"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["images"] == [
        {
            "filename": "figure1.png",
            "parent_slug": "alice-doc",
            "url": "/static/upload/alice-doc/figure1.png",
        }
    ]
    written = images_path / "alice-doc" / "figure1.png"
    assert written.is_file()
    assert written.read_bytes() == b"fake-png-bytes"


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_multiple_files(mock_get_release, logged_in_client, images_path):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
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

    assert response.status_code == 200
    filenames = [img["filename"] for img in response.get_json()["images"]]
    assert filenames == ["a.png", "b.jpg"]
    assert (images_path / "alice-doc" / "a.png").is_file()
    assert (images_path / "alice-doc" / "b.jpg").is_file()


def test_upload_image_missing_parent_slug(logged_in_client, images_path):
    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={"images": (BytesIO(b"x"), "x.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_upload_image_no_files(logged_in_client, images_path):
    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={"parent_slug": "alice-doc"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_unknown_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "missing-doc",
            "images": (BytesIO(b"x"), "x.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_unsupported_extension(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"x"), "evil.exe"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_oversized_file(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    big_payload = b"0" * (views.MAX_IMAGE_SIZE + 1)
    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(big_payload), "big.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert not (images_path / "alice-doc" / "big.png").exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_path_traversal_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "../escape"}])

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "../escape",
            "images": (BytesIO(b"x"), "x.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_collision_with_existing_file(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    (images_path / "alice-doc").mkdir()
    (images_path / "alice-doc" / "figure1.png").write_bytes(b"original")

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"replacement"), "Figure1.PNG"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]
    assert (images_path / "alice-doc" / "figure1.png").read_bytes() == b"original"


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_collision_within_batch(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
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

    assert response.status_code == 409
    assert (images_path / "alice-doc" / "figure1.png").read_bytes() == b"first"


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_returns_images_on_disk(
    mock_get_release, logged_in_client, images_path
):
    (images_path / "alice-doc").mkdir()
    (images_path / "alice-doc" / "a.png").write_bytes(b"a")
    (images_path / "alice-doc" / "b.jpg").write_bytes(b"b")
    (images_path / "alice-doc" / "ignored.txt").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(
        documents=[{"slug": "alice-doc"}, {"slug": "no-images-doc"}]
    )

    response = logged_in_client.get("/releases/cms/1/images")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["images"] == [
        {
            "filename": "a.png",
            "parent_slug": "alice-doc",
            "url": "/static/upload/alice-doc/a.png",
        },
        {
            "filename": "b.jpg",
            "parent_slug": "alice-doc",
            "url": "/static/upload/alice-doc/b.jpg",
        },
    ]


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_skips_documents_without_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(
        documents=[{"title": "no slug"}, {"slug": ""}]
    )

    response = logged_in_client.get("/releases/cms/1/images")
    assert response.status_code == 200
    assert response.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_when_no_directory_exists(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.get("/releases/cms/1/images")
    assert response.status_code == 200
    assert response.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_success_and_removes_empty_dir(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "a.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert not (slug_dir / "a.png").exists()
    assert not slug_dir.exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_keeps_non_empty_dir(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "a.png").write_bytes(b"a")
    (slug_dir / "b.png").write_bytes(b"b")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert response.status_code == 200
    assert (slug_dir / "b.png").exists()
    assert slug_dir.exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_unknown_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.delete("/releases/cms/1/images/other-doc/a.png")
    assert response.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_file_not_found(mock_get_release, logged_in_client, images_path):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/missing.png")
    assert response.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_success(mock_get_release, logged_in_client, images_path):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "New.PNG"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["image"] == {
        "filename": "new.png",
        "parent_slug": "alice-doc",
        "url": "/static/upload/alice-doc/new.png",
    }
    assert not (slug_dir / "old.png").exists()
    assert (slug_dir / "new.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_same_name_is_noop(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "same.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/same.png",
        json={"filename": "same.png"},
    )

    assert response.status_code == 200
    assert (slug_dir / "same.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_conflict_when_target_exists(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "old.png").write_bytes(b"a")
    (slug_dir / "new.png").write_bytes(b"b")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.png"},
    )

    assert response.status_code == 409
    assert (slug_dir / "old.png").is_file()
    assert (slug_dir / "new.png").read_bytes() == b"b"


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_source_not_found(mock_get_release, logged_in_client, images_path):
    (images_path / "alice-doc").mkdir()
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/missing.png",
        json={"filename": "new.png"},
    )
    assert response.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_missing_new_filename(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_unsupported_extension(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.exe"},
    )
    assert response.status_code == 400
    assert (slug_dir / "old.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_unknown_parent_slug(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/other-doc/old.png",
        json={"filename": "new.png"},
    )
    assert response.status_code == 404


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_filename_that_sanitizes_to_empty(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"x"), ".."),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_rejects_target_path_escape(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(views, "secure_filename", lambda _: "../escape.png")

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"x"), "anything.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert not (images_path / "escape.png").exists()


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_skips_doc_slug_path_traversal(
    mock_get_release, logged_in_client, images_path
):
    sibling = images_path.parent / "sibling-leak"
    sibling.mkdir(exist_ok=True)
    (sibling / "secret.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "../sibling-leak"}])

    response = logged_in_client.get("/releases/cms/1/images")

    assert response.status_code == 200
    assert response.get_json()["images"] == []


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rejects_parent_slug_path_traversal(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": ".."}])

    response = logged_in_client.delete("/releases/cms/1/images/../file.png")
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rejects_filename_that_sanitizes_to_empty(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/..")
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_rejects_target_path_escape(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    (images_path / "alice-doc").mkdir()
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(views, "secure_filename", lambda _: "../escape.png")

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/anything.png")
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_parent_slug_path_traversal(
    mock_get_release, logged_in_client, images_path
):
    mock_get_release.return_value = MagicMock(documents=[{"slug": ".."}])

    response = logged_in_client.put(
        "/releases/cms/1/images/../old.png",
        json={"filename": "new.png"},
    )
    assert response.status_code == 400


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_target_path_escape(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])
    monkeypatch.setattr(views, "secure_filename", lambda _: "../escape.png")

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.png"},
    )
    assert response.status_code == 400
    assert (slug_dir / "old.png").is_file()


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_rejects_new_filename_that_sanitizes_to_empty(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "old.png").write_bytes(b"a")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": ".."},
    )
    assert response.status_code == 400
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

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"img"), "photo.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert "Could not prepare upload directory" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_upload_image_save_oserror_returns_500(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir(mode=0o444)  # read-only: file.save() will raise OSError
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    response = logged_in_client.post(
        "/releases/cms/1/upload_image",
        data={
            "parent_slug": "alice-doc",
            "images": (BytesIO(b"img"), "photo.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert "Could not save image" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_iterdir_oserror_skips_directory(
    mock_get_release, logged_in_client, images_path
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "ok.png").write_bytes(b"x")

    mock_get_release.return_value = MagicMock(
        documents=[{"slug": "alice-doc"}, {"slug": "other-doc"}]
    )

    response = logged_in_client.get("/releases/cms/1/images")

    assert response.status_code == 200
    images = response.get_json()["images"]
    assert len(images) == 1
    assert images[0]["filename"] == "ok.png"


@patch("cernopendata.modules.releases.views._get_release")
def test_delete_image_unlink_oserror_returns_500(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "a.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        type(slug_dir / "a.png"),
        "unlink",
        lambda *a, **k: (_ for _ in ()).throw(OSError("locked")),
    )

    response = logged_in_client.delete("/releases/cms/1/images/alice-doc/a.png")

    assert response.status_code == 500
    assert "Could not delete image" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_rename_image_oserror_returns_500(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
    (slug_dir / "old.png").write_bytes(b"x")
    mock_get_release.return_value = MagicMock(documents=[{"slug": "alice-doc"}])

    monkeypatch.setattr(
        type(slug_dir / "old.png"),
        "rename",
        lambda *a, **k: (_ for _ in ()).throw(OSError("locked")),
    )

    response = logged_in_client.put(
        "/releases/cms/1/images/alice-doc/old.png",
        json={"filename": "new.png"},
    )

    assert response.status_code == 500
    assert "Could not rename image" in response.get_json()["error"]


@patch("cernopendata.modules.releases.views._get_release")
def test_list_images_iterdir_raising_oserror_logs_and_skips(
    mock_get_release, logged_in_client, images_path, monkeypatch
):
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
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
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
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
    slug_dir = images_path / "alice-doc"
    slug_dir.mkdir()
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
