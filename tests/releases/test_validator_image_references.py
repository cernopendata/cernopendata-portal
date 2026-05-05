from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.validations.image_references import (
    ValidImageReferences,
)


@pytest.fixture
def images_root(app, tmp_path, monkeypatch):
    """Override CERNOPENDATA_IMAGES_PATH to a tmp dir."""
    monkeypatch.setitem(app.config, "CERNOPENDATA_IMAGES_PATH", str(tmp_path))
    return tmp_path


def _doc(content, fmt="md", **extra):
    doc = {"body": {"content": content, "format": fmt}}
    doc.update(extra)
    return doc


def test_skips_documents_without_md_format(app, images_root):
    release = MagicMock()
    release.documents = [
        _doc('<img src="/static/upload/alice/missing.png">', fmt="html")
    ]
    assert ValidImageReferences().validate(release) == []


def test_skips_empty_or_missing_content(app, images_root):
    release = MagicMock()
    release.documents = [_doc(""), {"body": {"format": "md"}}, {}]
    assert ValidImageReferences().validate(release) == []


def test_uploaded_image_present_passes(app, images_root):
    (images_root / "alice").mkdir()
    (images_root / "alice" / "fig.png").write_bytes(b"a")

    release = MagicMock()
    release.documents = [_doc("![](/static/upload/alice/fig.png)")]
    assert ValidImageReferences().validate(release) == []


def test_uploaded_image_missing_reports_error(app, images_root):
    release = MagicMock()
    release.documents = [_doc("![alt](/static/upload/alice/missing.png)")]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert "Document 1" in errors[0]
    assert "/static/upload/alice/missing.png" in errors[0]
    assert "not found" in errors[0]


def test_html_img_tag_is_recognised(app, images_root):
    release = MagicMock()
    release.documents = [
        _doc('<img src="/static/upload/alice/missing.png" width="50%">')
    ]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert "/static/upload/alice/missing.png" in errors[0]


def test_static_docs_existing_image_passes(app, images_root):
    release = MagicMock()
    release.documents = [
        _doc('<img src="/static/docs/getting-started-with-alice/get_started_1.png">')
    ]
    assert ValidImageReferences().validate(release) == []


def test_static_docs_missing_image_reports_error(app, images_root):
    release = MagicMock()
    release.documents = [_doc('<img src="/static/docs/no-such-doc/missing.png">')]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert "/static/docs/no-such-doc/missing.png" in errors[0]


def test_external_url_is_ignored(app, images_root):
    release = MagicMock()
    release.documents = [_doc("![](https://example.com/img.png)")]
    assert ValidImageReferences().validate(release) == []


def test_unrecognised_local_path_reports_error(app, images_root):
    release = MagicMock()
    release.documents = [_doc('<img src="/uploads/foo.png">')]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert "unrecognised local path" in errors[0]


def test_path_traversal_in_url_is_rejected(app, images_root):
    release = MagicMock()
    release.documents = [_doc('<img src="/static/upload/../outside.png">')]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert "invalid path" in errors[0]


def test_empty_relative_path_after_prefix_is_rejected(app, images_root):
    release = MagicMock()
    release.documents = [_doc("![](/static/upload/)")]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert "invalid path" in errors[0]
    assert "/static/upload/" in errors[0]


def test_query_string_and_fragment_are_stripped(app, images_root):
    (images_root / "alice").mkdir()
    (images_root / "alice" / "fig.png").write_bytes(b"a")

    release = MagicMock()
    release.documents = [_doc("![](/static/upload/alice/fig.png?v=2#anchor)")]
    assert ValidImageReferences().validate(release) == []


def test_duplicate_urls_reported_once(app, images_root):
    release = MagicMock()
    release.documents = [
        _doc(
            '<img src="/static/upload/alice/missing.png">\n'
            "![](/static/upload/alice/missing.png)"
        )
    ]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1


def test_per_document_indexing(app, images_root):
    release = MagicMock()
    release.documents = [
        _doc("no images here"),
        _doc('<img src="/static/upload/alice/missing.png">'),
    ]
    errors = ValidImageReferences().validate(release)
    assert len(errors) == 1
    assert errors[0].startswith("Document 2:")


def test_extract_image_urls_combines_html_and_markdown():
    content = (
        '<img src="/static/upload/a/one.png">\n'
        "![](/static/upload/a/two.png)\n"
        '<IMG SRC="/static/upload/a/three.png">'
    )
    urls = ValidImageReferences._extract_image_urls(content)
    assert set(urls) == {
        "/static/upload/a/one.png",
        "/static/upload/a/two.png",
        "/static/upload/a/three.png",
    }
