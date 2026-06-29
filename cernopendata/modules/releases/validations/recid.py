"""Validation process."""

import re

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy import Integer, cast
from sqlalchemy.sql import func

from ..models import ReleaseMetadata
from .pid import PIDValidation


class ValidRecid(PIDValidation):
    """Check the record ids."""

    abstract = False
    name = "Valid recid"
    error_message = (
        "Each record must have a unique, unregistered recid in the correct format."
    )
    items_attr = "records"
    id_field = "recid"
    pid_type = "recid"

    def _recid_pattern(self, release):
        """Regex a recid must match: the experiment prefix followed by digits."""
        return re.compile(rf"^{re.escape(release.experiment)}-\d+$")

    def validate(self, release):
        """Check recids are present, unique, unregistered, and correctly formatted."""
        errors = super().validate(release)
        pattern = self._recid_pattern(release)
        for i, record in enumerate(release.records or []):
            recid = record.get("recid")
            if recid and not pattern.match(str(recid)):
                errors.append(
                    f"Entry {i + 1}: recid '{recid}' does not match the required format"
                )
        return errors

    def next_recid_start(self, release):
        """Find the next available recid."""
        # Highest recid assigned by releases
        max_release_recid = (
            db.session.query(func.max(ReleaseMetadata.max_recid))
            .filter(ReleaseMetadata.experiment == release.experiment)
            .scalar()
        ) or 0

        # Highest recid already registered as a PID
        max_registered_recid = (
            db.session.query(
                func.max(
                    cast(
                        func.split_part(PersistentIdentifier.pid_value, "-", 2), Integer
                    )
                )
            )
            .filter(
                PersistentIdentifier.pid_type == "recid",
                PersistentIdentifier.pid_value.like(f"{release.experiment}-%"),
            )
            .scalar()
        ) or 0

        return max(max_release_recid, max_registered_recid) + 1

    def fix(self, release):
        """Assign RECIDs to all records in the release."""
        counter = self.next_recid_start(release)
        duplicates = self._duplicate_pids(release)
        pattern = self._recid_pattern(release)

        for record in release.records:
            recid = record.get("recid")
            is_registered = recid in duplicates
            if not is_registered and pattern.match(str(recid or "")):
                continue
            if not is_registered and str(recid or "").isdigit():
                record["recid"] = f"{release.experiment}-{recid}"
            else:
                record["recid"] = f"{release.experiment}-{counter}"
                release.max_recid = counter
                counter += 1

        return []
