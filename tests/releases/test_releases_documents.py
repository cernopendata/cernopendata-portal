from unittest.mock import MagicMock

import pytest

from cernopendata.modules.releases.api import Release


def test_add_documents_triggers_validate(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(num_docs=0)
    r = Release(metadata)
    mock_validate = mocker.patch.object(r, "validate")

    user = MagicMock()
    r.add_documents([{"slug": "alice-data-2015"}], user)

    mock_validate.assert_called_once_with(user)


def test_add_documents_updates_count(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(documents=[{"slug": "existing-doc"}], num_docs=1)
    r = Release(metadata)
    mocker.patch.object(r, "validate")

    r.add_documents([{"slug": "new-doc-1"}, {"slug": "new-doc-2"}], MagicMock())

    assert metadata.num_docs == 3
    assert len(metadata.documents) == 3


def test_update_document_success(mocker, mock_jsonschemas, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")
    mocker.patch("cernopendata.modules.releases.api.flag_modified")

    metadata = mock_metadata(
        documents=[{"slug": "alice-data-2015", "title": "Old Title"}]
    )
    r = Release(metadata)
    mocker.patch.object(r, "validate")

    updated = {"slug": "alice-data-2015", "title": "New Title"}
    r.update_document("alice-data-2015", updated, MagicMock())

    assert metadata.documents[0]["title"] == "New Title"


def test_update_document_not_found(mocker, mock_metadata):
    mocker.patch("cernopendata.modules.releases.api.db.session")

    metadata = mock_metadata(documents=[{"slug": "existing-doc"}])
    r = Release(metadata)

    with pytest.raises(ValueError, match="not found"):
        r.update_document("nonexistent-slug", {"slug": "nonexistent-slug"}, MagicMock())
