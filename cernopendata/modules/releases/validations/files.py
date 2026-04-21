"""Validation process."""

import stat

import gfal2

from .base import Validation


class ValidFiles(Validation):
    """Check if the files have the proper metadata."""

    name = "File metadata"
    error_message = "Some of the files are missing the size or checksum"

    def validate(self, release):
        """Check that the files have size and checksum."""
        errors = []
        for i, record in enumerate(release.records):
            if "files" in record:
                for j, file in enumerate(record["files"]):
                    if "checksum" not in file or "size" not in file:
                        errors.append(
                            f"Entry {i + 1}, file {j + 1}: Missing size/checksum"
                        )
        return errors

    def _get_entry_details(self, ctx, url):
        """Given a url, return if the entry is a directory or a file. In case of file, return size anc checksum."""
        st = ctx.stat(url)

        if stat.S_ISDIR(st.st_mode):
            return True, None, None

        try:
            checksum = ctx.checksum(url, "ADLER32")
        except gfal2.GError:
            checksum = "UNKNOWN"

        return False, st.st_size, checksum

    def fix(self, release):
        """Add the size and checksum to the files."""
        ctx = gfal2.creat_context()
        errors = []
        for record in release.records:
            if "files" not in record:
                continue
            for file in record["files"]:
                if "checksum" in file and "size" in file:
                    continue
                try:
                    _, size, checksum = self._get_entry_details(
                        ctx, file["uri"].replace("root://", "https://")
                    )
                except Exception as e:
                    errors.append(f"Errors getting the metadata of {file['uri']}: {e}")
                    continue
                if "checksum" not in file:
                    file["checksum"] = checksum
                if "size" not in file:
                    file["size"] = size
        return errors
