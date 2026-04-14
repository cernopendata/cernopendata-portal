"""Validation process."""

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from ..models import ReleaseStatus
from .base import Validation


class ValidSlug(Validation):
    """Check the slugs of the documents in a release."""

    name = "Valid slug"
    error_message = (
        "The documents should have a unique slug that is not already registered."
    )
    applies_to = {"documents"}

    def validate(self, release):
        """Check that each document has a non-empty, unique, unregistered slug."""
        errors = []
        seen = {}
        for i, doc in enumerate(release.documents or []):
            slug = doc.get("slug")
            if not slug:
                errors.append(f"Document {i}: Missing or empty required field 'slug'")
                continue
            if slug in seen:
                errors.append(
                    f"Document {i}: Duplicate slug '{slug}' "
                    f"(also used by document {seen[slug]})"
                )
            else:
                seen[slug] = i

        if release.status != ReleaseStatus["STAGED"].value:
            used = self._duplicate_pids(release)
            if used:
                errors.append(f"Slugs already registered as docid: {', '.join(used)}")

        return errors

    def _duplicate_pids(self, release):
        """Return the slugs already registered as docid PIDs."""
        slugs = [
            doc.get("slug") for doc in (release.documents or []) if doc.get("slug")
        ]
        if not slugs:
            return []
        existing = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == "docid",
            PersistentIdentifier.pid_value.in_(slugs),
            PersistentIdentifier.status == PIDStatus.REGISTERED,
        ).all()
        return [pid.pid_value for pid in existing]

    def fix(self, release):
        """Auto-populate missing slugs from the doc's source filename."""
        errors = []
        for i, doc in enumerate(release.documents or []):
            if doc.get("slug"):
                continue
            source = doc.get("_source_filename")
            if not source:
                errors.append(
                    f"Document {i}: Cannot auto-fix slug — no source filename available"
                )
                continue
            slug = source.rsplit("/", 1)[-1]
            if slug.endswith(".json"):
                slug = slug[: -len(".json")]
            if not slug:
                errors.append(
                    f"Document {i}: Cannot derive a slug from source filename '{source}'"
                )
                continue
            doc["slug"] = slug
        return errors
