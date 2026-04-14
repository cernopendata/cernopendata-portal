"""Validation process."""

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from ..models import ReleaseStatus
from .base import Validation


class PIDValidation(Validation):
    """Abstract base class for validating identifier fields against PIDs."""

    abstract = True

    items_attr = None
    id_field = None
    pid_type = None

    def validate(self, release):
        """Check that each item has a non-empty, unique, unregistered identifier."""
        errors = []
        seen = {}
        items = getattr(release, self.items_attr) or []
        for i, item in enumerate(items):
            value = item.get(self.id_field)
            if not value:
                errors.append(
                    f"Entry {i + 1}: Missing or empty required field '{self.id_field}'"
                )
                continue
            if value in seen:
                errors.append(
                    f"Entry {i + 1}: Duplicate {self.id_field} '{value}' "
                    f"(also used by entry {seen[value] + 1})"
                )
            else:
                seen[value] = i

        if release.status != ReleaseStatus["STAGED"].value:
            used = self._duplicate_pids(release)
            if used:
                errors.append(f"{self.id_field}s already registered: {', '.join(used)}")

        return errors

    def _duplicate_pids(self, release):
        """Return identifiers already registered as PIDs."""
        items = getattr(release, self.items_attr) or []
        values = [item.get(self.id_field) for item in items if item.get(self.id_field)]
        if not values:
            return []
        existing = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == self.pid_type,
            PersistentIdentifier.pid_value.in_(values),
            PersistentIdentifier.status == PIDStatus.REGISTERED,
        ).all()
        return [pid.pid_value for pid in existing]
