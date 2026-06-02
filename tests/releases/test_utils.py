from unittest.mock import MagicMock, patch

from cernopendata.modules.releases.utils import (
    curator_experiments,
    user_info_with_cern_roles,
    user_payload_with_cern_roles,
)


def test_curator_experiments_returns_empty_for_unauthenticated_user():
    mock_user = MagicMock(is_authenticated=False)
    with patch("cernopendata.modules.releases.utils.current_user", mock_user):
        result = curator_experiments()
    assert result == {"curator_experiments": []}


def test_curator_experiments_returns_curator_experiment_names():
    mock_user = MagicMock(is_authenticated=True, id=1)
    mock_remote = MagicMock(extra_data={"cern_roles": ["cms-curator", "atlas-curator"]})
    with patch("cernopendata.modules.releases.utils.current_user", mock_user), patch(
        "cernopendata.modules.releases.utils.current_app"
    ) as mock_app, patch(
        "cernopendata.modules.releases.utils.RemoteAccount"
    ) as mock_ra:
        mock_app.config = {"CERN_APP_CREDENTIALS": {"consumer_key": "client-id"}}
        mock_ra.get.return_value = mock_remote
        result = curator_experiments()
    assert result == {"curator_experiments": ["cms", "atlas"]}


def test_curator_experiments_excludes_non_curator_roles():
    mock_user = MagicMock(is_authenticated=True, id=1)
    mock_remote = MagicMock(
        extra_data={"cern_roles": ["cms-curator", "cms-member", "unrelated-role"]}
    )
    with patch("cernopendata.modules.releases.utils.current_user", mock_user), patch(
        "cernopendata.modules.releases.utils.current_app"
    ) as mock_app, patch(
        "cernopendata.modules.releases.utils.RemoteAccount"
    ) as mock_ra:
        mock_app.config = {"CERN_APP_CREDENTIALS": {"consumer_key": "client-id"}}
        mock_ra.get.return_value = mock_remote
        result = curator_experiments()
    assert result == {"curator_experiments": ["cms"]}


def test_curator_experiments_returns_empty_when_no_curator_roles():
    mock_user = MagicMock(is_authenticated=True, id=1)
    mock_remote = MagicMock(extra_data={"cern_roles": ["cms-member"]})
    with patch("cernopendata.modules.releases.utils.current_user", mock_user), patch(
        "cernopendata.modules.releases.utils.current_app"
    ) as mock_app, patch(
        "cernopendata.modules.releases.utils.RemoteAccount"
    ) as mock_ra:
        mock_app.config = {"CERN_APP_CREDENTIALS": {"consumer_key": "client-id"}}
        mock_ra.get.return_value = mock_remote
        result = curator_experiments()
    assert result == {"curator_experiments": []}


def _patch_user_info(token_user_info, user_info=None, user=None, remote_user=None):
    """Return attribute-name → mock pairs for patch.multiple on the utils module."""
    return {
        "get_user_info": MagicMock(return_value=(token_user_info, user_info or {})),
        "current_app": MagicMock(
            config={"CERN_APP_CREDENTIALS": {"consumer_key": "client-id"}}
        ),
        "current_accounts": MagicMock(
            **{"datastore.get_user_by_email.return_value": user}
        ),
        "RemoteAccount": MagicMock(**{"get.return_value": remote_user}),
        "db": MagicMock(),
    }


def test_user_info_returns_expected_structure():
    token = {
        "sub": "jdoe",
        "email": "jdoe@cern.ch",
        "cern_person_id": "42",
        "cern_roles": ["cms-curator"],
    }
    user_info = {
        "home_institute": "CERN",
        "name": "John Doe",
        "cern_preferred_language": "fr",
    }
    patches = _patch_user_info(token, user_info)
    with patch.multiple("cernopendata.modules.releases.utils", **patches):
        result = user_info_with_cern_roles(MagicMock(name="cern"), MagicMock())
    assert result["user"]["email"] == "jdoe@cern.ch"
    assert result["user"]["profile"]["username"] == "jdoe"
    assert result["user"]["profile"]["full_name"] == "John Doe"
    assert result["user"]["profile"]["affiliations"] == "CERN"
    assert result["user"]["prefs"]["locale"] == "fr"
    assert result["external_id"] == "42"
    assert result["cern_roles"] == ["cms-curator"]


def test_user_info_falls_back_to_username_when_no_cern_person_id():
    token = {"sub": "jdoe", "email": "jdoe@cern.ch", "cern_roles": []}
    patches = _patch_user_info(token)
    with patch.multiple("cernopendata.modules.releases.utils", **patches):
        result = user_info_with_cern_roles(MagicMock(name="cern"), MagicMock())
    assert result["external_id"] == "jdoe"


def test_user_info_defaults_locale_to_english():
    token = {"sub": "jdoe", "email": "jdoe@cern.ch", "cern_roles": []}
    patches = _patch_user_info(token, user_info={})
    with patch.multiple("cernopendata.modules.releases.utils", **patches):
        result = user_info_with_cern_roles(MagicMock(name="cern"), MagicMock())
    assert result["user"]["prefs"]["locale"] == "en"


def test_user_info_updates_remote_account_cern_roles():
    token = {
        "sub": "jdoe",
        "email": "jdoe@cern.ch",
        "cern_roles": ["cms-curator"],
    }
    mock_remote = MagicMock(extra_data={})
    patches = _patch_user_info(token, user=MagicMock(), remote_user=mock_remote)
    with patch.multiple("cernopendata.modules.releases.utils", **patches):
        user_info_with_cern_roles(MagicMock(name="cern"), MagicMock())
    assert mock_remote.extra_data["cern_roles"] == ["cms-curator"]


def test_user_info_skips_remote_account_update_when_user_not_found():
    token = {
        "sub": "jdoe",
        "email": "unknown@example.com",
        "cern_roles": ["cms-curator"],
    }
    patches = _patch_user_info(token, user=None)
    mock_ra = patches["RemoteAccount"]
    with patch.multiple("cernopendata.modules.releases.utils", **patches):
        user_info_with_cern_roles(MagicMock(name="cern"), MagicMock())
    mock_ra.get.assert_not_called()


def test_user_payload_returns_expected_structure():
    mock_user = MagicMock(id=1, email="jdoe@cern.ch", roles=[])
    mock_user.confirmed_at.isoformat.return_value = "2024-01-01T00:00:00"
    mock_user.login_info.last_login_at = None
    mock_remote = MagicMock(extra_data={"cern_roles": ["cms-curator"]})
    with patch("cernopendata.modules.releases.utils.current_app") as mock_app, patch(
        "cernopendata.modules.releases.utils.RemoteAccount"
    ) as mock_ra, patch(
        "cernopendata.modules.releases.utils.role_to_dict", return_value={}
    ):
        mock_app.config = {"CERN_APP_CREDENTIALS": {"consumer_key": "client-id"}}
        mock_ra.get.return_value = mock_remote
        result = user_payload_with_cern_roles(mock_user)
    assert result["id"] == 1
    assert result["email"] == "jdoe@cern.ch"
    assert result["cern_roles"] == ["cms-curator"]
    assert result["last_login_at"] is None


def test_user_payload_formats_last_login_at():
    mock_user = MagicMock(id=1, email="jdoe@cern.ch", roles=[])
    mock_user.confirmed_at = None
    mock_user.login_info.last_login_at.isoformat.return_value = "2024-06-01T12:00:00"
    mock_remote = MagicMock(extra_data={"cern_roles": []})
    with patch("cernopendata.modules.releases.utils.current_app") as mock_app, patch(
        "cernopendata.modules.releases.utils.RemoteAccount"
    ) as mock_ra, patch(
        "cernopendata.modules.releases.utils.role_to_dict", return_value={}
    ):
        mock_app.config = {"CERN_APP_CREDENTIALS": {"consumer_key": "client-id"}}
        mock_ra.get.return_value = mock_remote
        result = user_payload_with_cern_roles(mock_user)
    assert result["last_login_at"] == "2024-06-01T12:00:00"
    assert result["confirmed_at"] is None
