from unittest.mock import MagicMock, patch

from cernopendata.modules.releases import tasks


@patch("cernopendata.modules.releases.tasks.User")
@patch("cernopendata.modules.releases.tasks.Release")
def test_stage_release_task_success(mock_release_cls, mock_user_cls):
    release = MagicMock()
    mock_release_cls.get.return_value = release
    user = MagicMock()
    mock_user_cls.query.get.return_value = user

    tasks.stage_release("cms", 1, 1)

    release.stage.assert_called_once_with(user)
    release.mark_staging_failed.assert_not_called()


@patch("cernopendata.modules.releases.tasks.current_app")
@patch("cernopendata.modules.releases.tasks.db")
@patch("cernopendata.modules.releases.tasks.User")
@patch("cernopendata.modules.releases.tasks.Release")
def test_stage_release_task_failure_marks_release(
    mock_release_cls, mock_user_cls, mock_db, mock_current_app
):
    release = MagicMock()
    release.stage.side_effect = RuntimeError("Broken release")
    mock_release_cls.get.return_value = release
    user = MagicMock()
    mock_user_cls.query.get.return_value = user

    tasks.stage_release("cms", 1, 1)

    mock_db.session.rollback.assert_called_once()
    release.mark_staging_failed.assert_called_once()
    message, failed_user = release.mark_staging_failed.call_args[0]
    assert "Broken release" in message
    assert failed_user is user


@patch("cernopendata.modules.releases.tasks.User")
@patch("cernopendata.modules.releases.tasks.Release")
def test_publish_release_task_success(mock_release_cls, mock_user_cls):
    release = MagicMock()
    mock_release_cls.get.return_value = release
    user = MagicMock()
    mock_user_cls.query.get.return_value = user

    tasks.publish_release("cms", 1, 1)

    release.publish.assert_called_once_with(user)
    release.mark_publishing_failed.assert_not_called()


@patch("cernopendata.modules.releases.tasks.current_app")
@patch("cernopendata.modules.releases.tasks.db")
@patch("cernopendata.modules.releases.tasks.User")
@patch("cernopendata.modules.releases.tasks.Release")
def test_publish_release_task_failure_marks_release(
    mock_release_cls, mock_user_cls, mock_db, mock_current_app
):
    release = MagicMock()
    release.publish.side_effect = RuntimeError("Broken release")
    mock_release_cls.get.return_value = release
    user = MagicMock()
    mock_user_cls.query.get.return_value = user

    tasks.publish_release("cms", 1, 1)

    mock_db.session.rollback.assert_called_once()
    release.mark_publishing_failed.assert_called_once()
    message, failed_user = release.mark_publishing_failed.call_args[0]
    assert "Broken release" in message
    assert failed_user is user


@patch("cernopendata.modules.releases.tasks.User")
@patch("cernopendata.modules.releases.tasks.Release")
def test_rollback_release_task_success(mock_release_cls, mock_user_cls):
    release = MagicMock()
    mock_release_cls.get.return_value = release
    user = MagicMock()
    mock_user_cls.query.get.return_value = user

    tasks.rollback_release("cms", 1, 1)

    release.rollback.assert_called_once_with(user)
    release.mark_rollback_failed.assert_not_called()


@patch("cernopendata.modules.releases.tasks.current_app")
@patch("cernopendata.modules.releases.tasks.db")
@patch("cernopendata.modules.releases.tasks.User")
@patch("cernopendata.modules.releases.tasks.Release")
def test_rollback_release_task_failure_marks_release(
    mock_release_cls, mock_user_cls, mock_db, mock_current_app
):
    release = MagicMock()
    release.rollback.side_effect = RuntimeError("Broken release")
    mock_release_cls.get.return_value = release
    user = MagicMock()
    mock_user_cls.query.get.return_value = user

    tasks.rollback_release("cms", 1, 1)

    mock_db.session.rollback.assert_called_once()
    release.mark_rollback_failed.assert_called_once()
    message, failed_user = release.mark_rollback_failed.call_args[0]
    assert "Broken release" in message
    assert failed_user is user
