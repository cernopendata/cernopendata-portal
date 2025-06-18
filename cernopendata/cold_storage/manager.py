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

"""Cold Storage Manager."""

import logging

from .api import ColdStorageActions, Transfer
from .catalog import Catalog
from .storage import Storage

logger = logging.getLogger(__name__)


class ColdStorageManager:
    """Class for the manager of the cold data transfers."""

    def __init__(self):
        """Initialize the class."""
        self._catalog = Catalog()
        self._storage = Storage()

    def _is_qos(self, file, action):
        """Check if a file is in a given QoS."""
        logger.debug(
            f"  Checking if the file {file['key']} is already {action.value}d..."
        )
        if action == ColdStorageActions.ARCHIVE:
            return "tags" in file and "uri_cold" in file["tags"]
        return "tags" not in file or "hot_deleted" not in file["tags"]

    def _move_record_file(
        self, record_uuid, file, action, move_function, register, force, dry
    ):
        """Create a new copy of the files of a record in a new QoS."""
        if self._is_qos(file, action):
            logger.debug(f" it is already {action.value}d")
            return "done", None
        if Transfer.is_scheduled(file["file_id"], action):
            logger.debug("It is already scheduled")
            return "scheduled", None
        source = (
            file["tags"]["uri_cold"]
            if action == ColdStorageActions.STAGE
            else file["uri"]
        )
        dest_file, method = self._storage.find_url(action, source)
        if not dest_file:
            logger.error(f"I can't find the cold url for {file['uri']}")
            return "error", None
        if not force:
            exists = method.exists_file(dest_file)
            if exists:
                if register:
                    if (
                        file["size"] == exists["size"]
                        and file["checksum"] == f"adler32:{exists['checksum']}"
                    ):
                        logger.debug(
                            "It exists, and has the same size and checksum. Registering it"
                        )
                        self._catalog.add_copy(
                            record_uuid, file["file_id"], action.value, dest_file
                        )
                        return "registered", None
                    logger.error(
                        "The size or the checksum is different: {file['size']} vs {exists['size']}"
                    )
                    return "inconsistent", None
                logger.error(
                    f"The file '{dest_file}' already exists in the destination storage... "
                    "Should it be registered (hint: `--register`)?"
                )
                return "to_register", None
        if dry:
            logger.info("Dry run: do not issue any transfer")
            return "dry", None
        entry = move_function(file)
        if not entry:
            return "error", None
        entry["record_uuid"] = record_uuid
        entry["key"] = file["key"]
        entry["file_id"] = file["file_id"]
        entry["size"] = file["size"]

        return "created", Transfer.create(entry)

    def _move_record(
        self, record_uuid, limit, action, move_function, register, force, dry
    ):
        """Internal function to move the fiels of a record."""
        # Let's find the files inside the record
        summary = {}
        transfers = []
        # Get the record
        record = self._catalog.get_record(record_uuid)
        if not record:
            return []
        for file in self._catalog.get_files_from_record(record):
            status, new_transfer = self._move_record_file(
                record.id, file, action, move_function, register, force, dry
            )
            summary[status] = summary.get(status, 0) + 1
            if new_transfer:
                transfers.append(new_transfer)
            if limit and len(transfers) >= limit:
                logger.info(f"Reached the limit {limit}. Going back")
                break
        if "registered" in summary:
            self._catalog.reindex_entries()
        logger.info(
            "Summary:"
            + ", ".join(f"{key}: {value}" for key, value in summary.items())
            + f"{len(transfers)} transfers have been issued"
        )
        return transfers

    def doOperation(self, action, record_uuid, limit, register, force, dry):
        """Internal function."""
        if action in [ColdStorageActions.ARCHIVE, ColdStorageActions.STAGE]:
            if action == ColdStorageActions.ARCHIVE:
                move_function = self._storage.archive
            else:
                move_function = self._storage.stage
            return self._move_record(
                record_uuid,
                limit,
                action,
                move_function,
                register,
                force,
                dry,
            )
        elif action == ColdStorageActions.CLEAR_HOT:
            return self.clear_hot(record_uuid, limit, dry)
        raise ValueError(
            f"The cold manager does not understand the operation '{action}'"
        )

    def clear_hot(self, record_uuid, limit, dry):
        """Remove the hot copy of a file that has a copy on cold storage."""
        # Let's find the files inside the record
        cleared = False
        record = self._catalog.get_record(record_uuid)
        if not record:
            return []
        for file in self._catalog.get_files_from_record(record, limit):
            if not self._is_qos(file, ColdStorageActions.ARCHIVE):
                logger.info(
                    "I don't want to remove the hot copy, since the cold does not exist!"
                )
                continue
            if not self._is_qos(file, ColdStorageActions.STAGE):
                logger.debug("the file is not in hot. Ignoring it")
                continue
            logger.debug(f"ready to be deleted")
            if not dry:
                self._storage.clear_hot(file["uri"])
            else:
                logger.info(
                    "Dry run: do not remove the file (but cleaning the repository)"
                )
            self._catalog.clear_hot(record, file["file_id"])
            cleared = True
        self._catalog.reindex_entries()
        return [cleared]

    def list(self, record_id):
        """Returns the location of the files for a particular record."""
        record = self._catalog.get_record(record_id)
        return self._catalog.get_files_from_record(record)
