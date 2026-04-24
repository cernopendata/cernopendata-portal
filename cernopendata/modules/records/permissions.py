"""CERN Open Data record permissions."""

import logging

from flask_login import current_user

from cernopendata.modules.releases.utils import curator_experiments

logger = logging.getLogger(__name__)


def record_read_permission_factory(record, *args, **kwargs):
    """Return a read permission for a record.

    By default, records are publicly accessible. If the record appears
    in a release that has not yet been published, access is restricted
    to curators of the corresponding experiment.
    """

    def can(self):
        prerelease = record.get("prerelease")
        if not prerelease:
            return True

        try:
            experiment, _ = prerelease.split("/", 1)
        except (ValueError, AttributeError):
            logger.error(
                f"Malformed prerelease field on record {record.get('recid')}: {prerelease}"
            )
            return False

        if not current_user.is_authenticated:
            return False

        return experiment in curator_experiments()["curator_experiments"]

    return type("RecordReadPermission", (), {"can": can})()
