from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases.models import ReleaseMetadata, ReleaseStatus


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
