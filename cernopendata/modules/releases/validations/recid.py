"""Validation process."""

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.sql import func

from ..models import ReleaseMetadata, ReleaseStatus
from .base import Validation


class ValidRecid(Validation):
    """Check the record ids."""

    name = "valid recid"
    error_message = "The records should have record id that do not exist."

    def validate(self, release):
        """Check that all the entries have recid, and that they are not duplicated."""
        errors = []
        for i, entry in enumerate(release.records):
            if "recid" not in entry or not entry["recid"]:
                errors.append(f"Entry {i + 1}: Missing or empty required field 'recid'")

        # If the release is not STAGED, check for duplicates
        if release.status != ReleaseStatus["STAGED"].value:
            used = self._duplicate_pids(release)
            if used:
                errors.append(f"RECIDs already registered: {', '.join(used)}")

        return errors

    def _duplicate_pids(self, release):
        """Check the pids that are duplicated."""
        recids = [r.get("recid") for r in release.records if r.get("recid")]
        existing_pid = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == "recid",
            PersistentIdentifier.pid_value.in_(recids),
            PersistentIdentifier.status == "R",
        ).all()
        if existing_pid:
            used = [pid.pid_value for pid in existing_pid]
            return used
        return []

    def next_recid_start(self, release):
        """Find the next available recid."""
        max_value = (
            db.session.query(func.max(release.max_recid))
            .filter(ReleaseMetadata.experiment == release.experiment)
            .scalar()
        )
        return (max_value or 0) + 1

    def fix(self, release):
        """Assign RECIDs to all records in the release."""
        counter = self.next_recid_start(release)
        duplicates = self._duplicate_pids(release)

        for record in release.records:
            if "recid" not in record or record["recid"] in duplicates:
                counter += 1
                record["recid"] = f"{release.experiment}-{counter}"

        if release.records:
            release.max_recid = counter
        return []
