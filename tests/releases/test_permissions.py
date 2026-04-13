import logging
from unittest.mock import MagicMock, patch

from cernopendata.modules.records.permissions import record_read_permission_factory


def make_permission(record):
    return record_read_permission_factory(record)


def test_public_record_is_readable():
    permission = make_permission({"recid": 1, "title": "Public record"})
    assert permission.can() is True


def test_empty_prerelease_is_readable():
    permission = make_permission({"recid": 2, "prerelease": ""})
    assert permission.can() is True


def test_none_prerelease_is_readable():
    permission = make_permission({"recid": 3, "prerelease": None})
    assert permission.can() is True


def test_prerelease_denies_anonymous_user():
    mock_user = MagicMock()
    mock_user.is_authenticated = False

    with patch("cernopendata.modules.records.permissions.current_user", mock_user):
        permission = make_permission({"recid": 10, "prerelease": "cms/v1"})
        assert permission.can() is False


def test_prerelease_allows_experiment_curator():
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch(
        "cernopendata.modules.records.permissions.current_user", mock_user
    ), patch(
        "cernopendata.modules.records.permissions.curator_experiments",
        return_value={"curator_experiments": ["cms"]},
    ):
        permission = make_permission({"recid": 11, "prerelease": "cms/v1"})
        assert permission.can() is True


def test_prerelease_denies_curator_of_different_experiment():
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch(
        "cernopendata.modules.records.permissions.current_user", mock_user
    ), patch(
        "cernopendata.modules.records.permissions.curator_experiments",
        return_value={"curator_experiments": ["atlas"]},
    ):
        permission = make_permission({"recid": 12, "prerelease": "cms/v1"})
        assert permission.can() is False


def test_prerelease_denies_authenticated_non_curator():
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch(
        "cernopendata.modules.records.permissions.current_user", mock_user
    ), patch(
        "cernopendata.modules.records.permissions.curator_experiments",
        return_value={"curator_experiments": []},
    ):
        permission = make_permission({"recid": 13, "prerelease": "cms/v1"})
        assert permission.can() is False


def test_prerelease_allows_curator_of_multiple_experiments():
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch(
        "cernopendata.modules.records.permissions.current_user", mock_user
    ), patch(
        "cernopendata.modules.records.permissions.curator_experiments",
        return_value={"curator_experiments": ["cms", "atlas", "lhcb"]},
    ):
        for experiment in ["cms", "atlas", "lhcb"]:
            permission = make_permission(
                {"recid": 20, "prerelease": f"{experiment}/v1"}
            )
            assert permission.can() is True


def test_malformed_prerelease_no_slash_returns_false(caplog):
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch("cernopendata.modules.records.permissions.current_user", mock_user):
        with caplog.at_level(
            logging.ERROR, logger="cernopendata.modules.records.permissions"
        ):
            permission = make_permission({"recid": 30, "prerelease": "noslash"})
            assert permission.can() is False

    assert any("Malformed prerelease" in r.message for r in caplog.records)


def test_malformed_prerelease_non_string_returns_false(caplog):
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch("cernopendata.modules.records.permissions.current_user", mock_user):
        with caplog.at_level(
            logging.ERROR, logger="cernopendata.modules.records.permissions"
        ):
            permission = make_permission({"recid": 31, "prerelease": 12345})
            assert permission.can() is False

    assert any("Malformed prerelease" in r.message for r in caplog.records)


def test_prerelease_with_extra_slashes_uses_first_segment():
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    with patch(
        "cernopendata.modules.records.permissions.current_user", mock_user
    ), patch(
        "cernopendata.modules.records.permissions.curator_experiments",
        return_value={"curator_experiments": ["cms"]},
    ):
        permission = make_permission({"recid": 40, "prerelease": "cms/2024/v2"})
        assert permission.can() is True
