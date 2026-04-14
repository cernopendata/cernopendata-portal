"""Validation process."""

from .pid import PIDValidation


class ValidSlug(PIDValidation):
    """Check the slugs of the documents in a release."""

    abstract = False
    name = "Valid slug"
    error_message = (
        "The documents should have a unique slug that is not already registered."
    )
    applies_to = {"documents"}
    items_attr = "documents"
    id_field = "slug"
    pid_type = "docid"

    def fix(self, release):
        """Auto-populate missing slugs from the doc's source filename."""
        errors = []
        for i, doc in enumerate(release.documents or []):
            if doc.get("slug"):
                continue
            source = doc.get("_source_filename")
            if not source:
                errors.append(
                    f"Entry {i + 1}: Cannot auto-fix slug — no source filename available"
                )
                continue
            slug = source.rsplit("/", 1)[-1]
            if slug.endswith(".json"):
                slug = slug[: -len(".json")]
            if not slug:
                errors.append(
                    f"Entry {i + 1}: Cannot derive a slug from source filename '{source}'"
                )
                continue
            doc["slug"] = slug
        return errors
