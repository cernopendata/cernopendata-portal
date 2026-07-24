"""Celery tasks for the release curation process."""

from celery import shared_task
from flask import current_app
from invenio_accounts.models import User
from invenio_db import db

from .api import Release


@shared_task
def stage_release(experiment, release_id, user_id):
    """Stage a release."""
    release = Release.get(experiment, release_id)
    user = User.query.get(user_id)
    try:
        release.stage(user)
    except Exception as exc:
        current_app.logger.exception("Staging release %s failed", release_id)
        db.session.rollback()
        release = Release.get(experiment, release_id)
        release.mark_staging_failed(str(exc), user)


@shared_task
def publish_release(experiment, release_id, user_id):
    """Publish a release."""
    release = Release.get(experiment, release_id)
    user = User.query.get(user_id)
    try:
        release.publish(user)
    except Exception as exc:
        current_app.logger.exception("Publishing release %s failed", release_id)
        db.session.rollback()
        release = Release.get(experiment, release_id)
        release.mark_publishing_failed(str(exc), user)


@shared_task
def rollback_release(experiment, release_id, user_id):
    """Roll back a release."""
    release = Release.get(experiment, release_id)
    user = User.query.get(user_id)
    try:
        release.rollback(user)
    except Exception as exc:
        current_app.logger.exception("Rolling back release %s failed", release_id)
        db.session.rollback()
        release = Release.get(experiment, release_id)
        release.mark_rollback_failed(str(exc), user)
