# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2024 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Open Data Portal; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""Expand Files validation."""
import gfal2

from .files import ValidFiles


class FileExpansionError(Exception):
    """Exception for the File Expansion."""

    pass


class CheckExpandDirectories(ValidFiles):
    """Validation to check for duplicate files."""

    name = "Expand directories"
    error_message = (
        "Some of the entries in the records are directories instead of files"
    )

    modified = False

    def _walk(self, ctx, base_uri):
        """Recursively yield all file paths under base_uri."""
        http_uri = base_uri.replace("root://", "https://")
        try:
            entries = ctx.listdir(http_uri)
        except gfal2.GError:
            raise FileExpansionError

        for entry in entries:
            full_uri = f"{base_uri}/{entry}"
            isDir, size, checksum = self._get_entry_details(ctx, f"{http_uri}/{entry}")

            # If it’s a directory, recurse
            if isDir:
                yield from walk(full_uri)
            else:
                yield {"uri": full_uri, "size": size, "checksum": checksum}

    def validate(self, release):
        """Check if there are any directories as input for a record."""
        errors = []
        for record in release.records:
            if "files" not in record:
                continue

            for file in record["files"]:
                if "uri" in file and file["uri"].endswith("*"):
                    errors.append(f"The record {i} has a path like {file['uri']}")
        return errors

    def fix(self, release):
        """Fix the records that contain directories."""
        errors = []
        ctx = gfal2.creat_context()

        for record in release.records:
            if "files" not in record:
                continue

            new_files = []
            for file in record["files"]:
                if "uri" in file and file["uri"].endswith("*"):
                    basedir = file["uri"][:-1]
                    try:
                        for f in self._walk(ctx, basedir):
                            new_files.append(f)
                    except FileExpansionError:
                        errors.append(
                            f"Error accessing the path {basedir} while expanding the file names"
                        )

            # Append new files and remove the wildcard entry
            if new_files:
                # Remove the wildcard entry itself
                record["files"] = [
                    f
                    for f in record["files"]
                    if not (f.get("uri") and f["uri"].endswith("*"))
                ]
                record["files"].extend(new_files)
        return errors
