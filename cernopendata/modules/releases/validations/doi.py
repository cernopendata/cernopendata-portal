"""Validation that record DOIs use the correct prefix and have unique suffixes."""

from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from ...datacite.utils import generate_doi
from .base import Validation


class ValidDoi(Validation):
    """Check that record DOIs use the correct prefix and have unique suffixes."""

    name = "Valid DOI"
    error_message = "DOIs must use the correct prefix and have a unique suffix."
    applies_to = {"records"}

    def _validate_prefix(self):
        """Return True only on the production instance, where DOI prefixes are validated."""
        return current_app.config["INSTANCE_NAME"] == "opendata"

    def validate(self, release):
        """Check the prefix and suffix uniqueness of every record that has a DOI."""
        prefix = str(current_app.config.get("PIDSTORE_DATACITE_DOI_PREFIX"))
        validate_prefix = self._validate_prefix()
        errors = []
        used_suffixes = {}
        for i, record in enumerate(release.records or []):
            doi = record.get("doi")
            if not doi:
                continue
            doi_prefix, separator, suffix = doi.partition("/")
            if not separator or not suffix:
                errors.append(f"Entry {i + 1}: Malformed DOI '{doi}'")
                continue
            if validate_prefix and doi_prefix != prefix:
                errors.append(
                    f"Entry {i + 1}: DOI prefix '{doi_prefix}' does not match "
                    f"the prefix '{prefix}'"
                )
            if suffix in used_suffixes:
                errors.append(
                    f"Entry {i + 1}: Duplicate DOI suffix '{suffix}' "
                    f"(also used by entry {used_suffixes[suffix] + 1})"
                )
            else:
                used_suffixes[suffix] = i

        for suffix in self._registered_suffixes(prefix, list(used_suffixes)):
            errors.append(f"DOI suffix already registered: {suffix}")

        return errors

    def fix(self, release):
        """Replace invalid DOIs.

        - in case of an invalid, duplicate or missing suffix, mint a new DOI
        - wrong prefix is validated and replaced only in production
        """
        prefix = str(current_app.config.get("PIDSTORE_DATACITE_DOI_PREFIX"))
        validate_prefix = self._validate_prefix()
        records = release.records or []

        all_suffixes = [
            record["doi"].partition("/")[2]
            for record in records
            if record.get("doi") and "/" in record["doi"]
        ]
        registered_suffixes = set(self._registered_suffixes(prefix, all_suffixes))

        used_suffixes = set()
        for record in records:
            doi = record.get("doi")
            if not doi:
                continue
            doi_prefix, separator, suffix = doi.partition("/")
            if not separator or not suffix:
                record["doi"] = generate_doi(prefix, release.experiment)
                used_suffixes.add(record["doi"].partition("/")[2])
                continue
            if validate_prefix and doi_prefix != prefix:
                record["doi"] = f"{prefix}/{suffix}"
            if suffix in used_suffixes or suffix in registered_suffixes:
                record["doi"] = generate_doi(prefix, release.experiment)
                suffix = record["doi"].partition("/")[2]
            used_suffixes.add(suffix)
        return self.validate(release)

    @staticmethod
    def _registered_suffixes(prefix, suffixes):
        """Return suffixes whose '{prefix}/{suffix}' DOI is already a registered PID."""
        if not suffixes:
            return []
        candidates = {f"{prefix}/{suffix}": suffix for suffix in suffixes}
        existing = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == "doi",
            PersistentIdentifier.pid_value.in_(list(candidates)),
            PersistentIdentifier.status == PIDStatus.REGISTERED,
        ).all()
        return [candidates[pid.pid_value] for pid in existing]
