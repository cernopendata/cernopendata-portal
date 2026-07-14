"""Validation process."""

import stat

import gfal2

from .base import Validation


class ValidFiles(Validation):
    """Check if the files have the proper metadata."""

    name = "File metadata"
    error_message = (
        "Some of the files are missing the size, or have a missing or invalid checksum"
    )

    @staticmethod
    def _has_checksum_prefix(checksum):
        """Return whether the checksum has the ``algorithm:value`` shape with both parts non-empty."""
        parts = str(checksum).split(":")
        return len(parts) == 2 and all(parts)

    def validate(self, release):
        """Check that the files have size and a checksum in the correct format."""
        errors = []
        for i, record in enumerate(release.records):
            if "files" in record:
                for j, file in enumerate(record["files"]):
                    file_label = f"Entry {i + 1}, file {j + 1}"
                    if "size" not in file:
                        errors.append(f"{file_label}: Missing size")
                    if "checksum" not in file:
                        errors.append(f"{file_label}: Missing checksum")
                    elif not self._has_checksum_prefix(file["checksum"]):
                        errors.append(
                            f"{file_label}: Invalid checksum '{file['checksum']}'"
                        )
        return errors

    def _get_entry_details(self, ctx, url):
        """Given a url, return if the entry is a directory or a file. In case of file, return size and checksum."""
        st = ctx.stat(url)

        if stat.S_ISDIR(st.st_mode):
            return True, None, None

        try:
            checksum = f"adler32:{ctx.checksum(url, 'ADLER32')}"
        except gfal2.GError:
            checksum = None

        return False, st.st_size, checksum

    def fix(self, release):
        """Add the size and checksum to the files."""
        ctx = gfal2.creat_context()
        errors = []
        for record in release.records:
            if "files" not in record:
                continue
            for file in record["files"]:
                valid_checksum = self._has_checksum_prefix(file.get("checksum", ""))
                if valid_checksum and "size" in file:
                    continue
                try:
                    _, size, checksum = self._get_entry_details(
                        ctx, file["uri"].replace("root://", "https://")
                    )
                except Exception as e:
                    errors.append(f"Errors getting the metadata of {file['uri']}: {e}")
                    continue
                if not valid_checksum and checksum:
                    file["checksum"] = checksum
                if "size" not in file:
                    file["size"] = size
        return errors
