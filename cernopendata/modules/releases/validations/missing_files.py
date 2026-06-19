"""Missing files validation."""

from .base import Validation


class MissingFiles(Validation):
    """Check that records claiming files actually provide them."""

    name = "Missing files"
    error_message = "Some records report having files, but none were provided."

    def validate(self, release):
        """Flag records that report having files but provide none."""
        errors = []
        for i, record in enumerate(release.records):
            number_files = (record.get("distribution") or {}).get("number_files") or 0
            if (
                number_files
                and not record.get("files")
                and "rucio_dataset" not in record
            ):
                errors.append(
                    f"Entry {i + 1} reports having {number_files} files "
                    f"but none were provided."
                )
        return errors
