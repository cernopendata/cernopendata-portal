"""Validation process."""

import re

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
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
        return re.compile(rf"^{re.escape(release.experiment)}-(\d+)$")

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
        errors.extend(
            f"Entry {i + 1}: recid '{recid}' collides with existing recid '{existing}'"
            for i, recid, existing in self._numeric_collisions(release)
        )
        return errors

    def _numeric_collisions(self, release):
        """Recids whose number duplicates an existing numeric recid."""
        pattern = self._recid_pattern(release)
        recid_by_number = {}
        for i, record in enumerate(release.records or []):
            match = pattern.match(str(record.get("recid") or ""))
            if match:
                recid_by_number[match.group(1)] = (i, record["recid"])
        if not recid_by_number:
            return []

        existing = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == self.pid_type,
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_value.in_(list(recid_by_number)),
        ).all()

        collisions = []
        for pid in existing:
            i, recid = recid_by_number[pid.pid_value]
            collisions.append((i, recid, pid.pid_value))
        return collisions

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

        # Highest numeric recid
        max_numeric_recid = (
            db.session.query(
                func.max(
                    cast(
                        func.substring(PersistentIdentifier.pid_value, r"^\d+$"),
                        Integer,
                    )
                )
            )
            .filter(PersistentIdentifier.pid_type == "recid")
            .scalar()
        ) or 0

        return max(max_release_recid, max_registered_recid, max_numeric_recid) + 1

    def fix(self, release):
        """Assign RECIDs to all records in the release."""
        counter = self.next_recid_start(release)
        duplicates = self._duplicate_pids(release)
        colliding = {recid for _, recid, _ in self._numeric_collisions(release)}
        pattern = self._recid_pattern(release)

        for record in release.records:
            recid = record.get("recid")
            is_registered = recid in duplicates
            has_numeric_collision = recid in colliding
            if (
                not is_registered
                and not has_numeric_collision
                and pattern.match(str(recid or ""))
            ):
                continue
            if not is_registered and str(recid or "").isdigit():
                record["recid"] = f"{release.experiment}-{recid}"
            else:
                record["recid"] = f"{release.experiment}-{counter}"
                release.max_recid = counter
                counter += 1

        return []
