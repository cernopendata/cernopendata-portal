from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases.models import ReleaseMetadata, ReleaseStatus


def _raises(exception):
    """Return a callable that raises ``exception`` when called with any arguments."""

    def _raise(*args, **kwargs):
        raise exception

    return _raise


@pytest.fixture
def dummy_metadata():
    """Return a fresh ReleaseMetadata object for tests."""
    return ReleaseMetadata(
        name="dummy_release",
        experiment="cms",
        records=[],
        validations=[],
        status=ReleaseStatus.DRAFT.value,
    )


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


@pytest.fixture
def mock_jsonschemas(mocker):
    """Patch current_app with invenio-jsonschemas returning 'schema-url'."""
    mock_app = mocker.patch("cernopendata.modules.releases.api.current_app")
    mock_app.extensions = {
        "invenio-jsonschemas": MagicMock(
            path_to_url=MagicMock(return_value="schema-url")
        )
    }
    return mock_app


@pytest.fixture
def mock_metadata():
    """Return a factory for configurable mock ReleaseMetadata objects."""

    def _factory(records=None, documents=None, **overrides):
        meta = MagicMock()
        meta.records = records if records is not None else []
        meta.documents = documents if documents is not None else []
        for key, value in overrides.items():
            setattr(meta, key, value)
        return meta

    return _factory
