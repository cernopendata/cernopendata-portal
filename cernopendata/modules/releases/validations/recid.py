"""Validation process."""

from invenio_db import db
from sqlalchemy.sql import func

from ..models import ReleaseMetadata
from .pid import PIDValidation


class ValidRecid(PIDValidation):
    """Check the record ids."""

    abstract = False
    name = "Valid recid"
    error_message = "The records should have record id that do not exist."
    items_attr = "records"
    id_field = "recid"
    pid_type = "recid"

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
