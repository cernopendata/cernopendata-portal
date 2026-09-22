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
            direct_files = len(record.get("files", []))
            file_indices = sum(
                len(item.get("files", [])) for item in record.get("_file_indices", [])
            )
            if (
                number_files
                and number_files != direct_files + file_indices
                and "rucio_dataset" not in record
            ):
                errors.append(
                    f"Entry {i + 1} reports having {number_files} files. There are {direct_files} files "
                    f"and {file_indices}."
                )
        return errors
