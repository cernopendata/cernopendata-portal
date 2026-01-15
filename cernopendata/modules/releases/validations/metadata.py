"""Validation process."""

from datetime import datetime

from flask_login import current_user

from .base import Validation


class ValidMetadata(Validation):
    """Check some common fields of the records."""

    name = "Valid standard fields"
    error_message = "Some records are missing some of the standard fields"

    COMMON_METADATA_FIELDS = ["license", "publisher", "date_published"]

    def validate(self, release):
        """Validate the records."""
        errors = []
        for i, record in enumerate(release.records):
            for field in ValidMetadata.COMMON_METADATA_FIELDS:
                if field not in record or record[field] in (None, ""):
                    errors.append(f"Entry {i + 1}: Missing {field}")
        return errors

    def fix(self, release):
        """Fix the incorrect records."""
        release.bulk_update(
            {
                "set": {
                    "experiment": [release._metadata.experiment.upper()],
                    "publisher": "CERN Open Data Portal",
                    "license": {"attribution": "CC0-1.0"},
                    "date_published": f"{datetime.now().year}",
                }
            },
            current_user,
        )
        return []
