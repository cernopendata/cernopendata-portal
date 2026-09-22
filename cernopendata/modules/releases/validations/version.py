"""Validation process for the version."""

import re

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sqlalchemy import Integer, cast
from sqlalchemy.sql import func

from ..models import ReleaseMetadata, ReleaseStatus
from .base import Validation
from ...records.api import OpenDataRecord


class ValidVersion(Validation):
    """Check the version."""

    name = "Valid version"
    error_message = "A record should start with version 1. Then, the number increments one at a time."

    def validate(self, release):
        """Check the version of the records."""
        errors = []
        for i, record in enumerate(release.records or []):
            version = record.get("version")
            if not version:
                errors.append(
                    f"Entry {i + 1}: Missing or empty required field 'version'"
                )
                continue

            if not isinstance(version, int) or isinstance(version, bool) or version < 1:
                errors.append(f"Entry {i + 1}: version must be a positive integer")
                continue
            if version > 1:
                # Ensuring that the version-1 is already defined
                # The corner case of the first version of the document should already be covered by the pid validation
                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value=f"{record.get('recid')}-v{version-1}"
                ).first()
                if not pid:
                    errors.append(
                        f"The version v{version-1} of {record.get('recid')} does not exist"
                    )
            pid = PersistentIdentifier.query.filter_by(
                pid_type="recid", pid_value=f"{record.get('recid')}-v{version}"
            ).first()
            if pid:
                errors.append(
                    f"The version v{version-1} of {record.get('recid')} already exists"
                )
        return errors

    def fix(self, release):
        """Assign versions to all records in the release."""
        for record in release.records:
            recid = record.get("recid")
            previous_version = OpenDataRecord.get_latest_version(recid)
            if not previous_version:
                previous_version = 0
            version = record.get("version") or 1
            if version == previous_version + 1:
                continue

            record["version"] = previous_version + 1

        return []
