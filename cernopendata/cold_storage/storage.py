# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017-2025 CERN.
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

"""Cold Storage storage interface."""
import logging
import os
import re
import gfal2

from invenio_db import db
from sqlalchemy import literal

from .api import ColdStorageActions, Transfer
from .models import Location
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Storage:
    """Class to deal with the storage of the files."""

    @classmethod
    def find_url(cls, action, file):
        """Identify the URL that a given file should have."""
        column = (
            Location.cold_path
            if action == ColdStorageActions.STAGE
            else Location.hot_path
        )

        location = (
            db.session.query(Location)
            .filter(literal(file).startswith(column))
            .order_by(db.func.length(column).desc())  # Most specific match first
            .first()
        )
        if location:
            prefix = (
                location.cold_path
                if action == ColdStorageActions.STAGE
                else location.hot_path
            )
            target = (
                location.hot_path
                if action == ColdStorageActions.STAGE
                else location.cold_path
            )
            return file.replace(prefix, target), Transfer.load_class(
                location.manager_class
            )
        return None, None

    def archive(self, file):
        """Create a cold copy for a file."""
        logger.debug(f"Archiving a file")
        filename = file["uri"]
        dest_file, transfer = Storage.find_url(ColdStorageActions.ARCHIVE, filename)
        if not dest_file:
            logger.error(f"WE CAN'T GUESS THE destination path :( of {filename}")
            return []
        id = transfer.archive(filename.replace("root://", "https://"), dest_file)
        if not id:
            return []
        return {
            "action": ColdStorageActions.ARCHIVE.value,
            "new_filename": dest_file,
            "filename": filename,
            "method": transfer.__class__.__module__,
            "method_id": id,
        }

    def stage(self, file):
        """Create a hot copy for a file."""
        filename = file["tags"]["uri_cold"]
        dest_file, transfer = Storage.find_url(
            ColdStorageActions.STAGE, filename.replace("root://", "https://")
        )
        logger.debug(f" Staging it")
        id = transfer.stage(filename, dest_file)
        if not id:
            logger.error("Error creating the transfer")
            return []
        return {
            "method_id": id,
            "method": transfer.__class__.__module__,
            "action": ColdStorageActions.STAGE.value,
            "new_filename": dest_file,
            "filename": filename,
        }

    def clear_hot(self, filename):
        """Clear the hot copy of a file."""
        path = re.sub("^((root)|(file))://[^/]*/", "/", filename)
        try:
            os.remove(path)
            return True
        except Exception as e:
            logger.error(f"Error deleting the file {path} (from {filename}) :*( {e}")
        return False

    @classmethod
    def verify_file(cls, uri: str, size: int, checksum: str) -> (bool, str):
        """Check if a file exists and has the given size and checksum."""
        parsed = urlparse(uri)

        if parsed.scheme in ("root", "https"):
            ctx = gfal2.creat_context()
            # gfal needs https protocol, instead of root.
            filename = uri.replace("root://", "https://")
            logger.debug(f"Checking with gfal if {filename} exists")
            try:
                info = ctx.stat(filename)
                if info.st_size != size:
                    return False, "different size"
                file_checksum = ctx.checksum(filename, "ADLER32")
                if checksum != f"adler32:{file_checksum}":
                    return False, "different checksum"
                return True, None
            except Exception as e:
                return False, "File does not exist"
        elif parsed.scheme == "" or parsed.scheme == "file":
            return cls._verify_file(parsed.path, size, checksum)
        else:
            raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
