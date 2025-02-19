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

import datetime
import time
from datetime import datetime
from os import getpid

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.cold_storage.models import Transfer, TransferRequest

from .catalog import Catalog
from .storage import Storage


class ColdStorageManager:
    """Class for the manager of the cold data transfers."""

    def __init__(self, app=None, debug=False):
        """Initialize the class."""
        self._catalog = Catalog(debug=debug)
        self._storage = Storage(app)

    def _is_qos(self, file, qos):
        """Check if a file is in a given QoS."""
        print(f"  Checking if the file {file['key']} is already {qos}...", end="")
        if qos == "cold":
            return "tags" in file and "uri_cold" in file["tags"]
        return "tags" not in file or "hot_deleted" not in file["tags"]

    def _move_record_entry(
        self, record_uuid, file, qos, move_function, register, check_exists, dry
    ):
        """Create a new copy of the files of a record in a new QoS."""
        if self._is_qos(file, qos):
            print(f" it is already {qos}")
            return []

        if Transfer().is_scheduled(file["file_id"], qos):
            print("It is already scheduled")
            return []
        dest_file, method = self._storage.find_cold_url(file["uri"])
        if not dest_file:
            print(f"I can't find the cold url for {file['uri']}")
            return []
        if check_exists:
            exists = method.exists_file(dest_file)
            if exists:
                if register:
                    if (
                        file["size"] == exists["size"]
                        and file["checksum"] == f"adler32:{exists['checksum']}"
                    ):
                        print(
                            "It exists, and has the same size and checksum. Registering it"
                        )
                        return [
                            Transfer.create_transfer(
                                {
                                    "record_uuid": record_uuid,
                                    "key": file["key"],
                                    "file_id": file["file_id"],
                                    "method": "cernopendata.cold_storage.transfer.cp",
                                    "new_qos": qos,
                                    "new_filename": dest_file,
                                }
                            )
                        ]
                    print(
                        "The size or the checksum is different: {file['size']} vs {exists['size']}"
                    )
                    return []
                print(
                    "The file already exists in the destination storage... "
                    "Should it be registered (hint: `--register`)?"
                )
                return []
        if dry:
            print("Dry run: do not issue any transfer")
            return []
        entry = move_function(file)
        if not entry:
            print("Let's return without storing it")
            return []
        entry["record_uuid"] = record_uuid
        entry["key"] = file["key"]
        entry["file_id"] = file["file_id"]

        return [Transfer.create_transfer(entry)]

    def _move_record(
        self, record_uuid, limit, qos, move_function, register, check_exists, dry
    ):
        """Internal function to move the fiels of a record."""
        # Let's find the files inside the record
        transfers = []
        # Get the record
        record = self._catalog.get_record(record_uuid)
        if not record:
            return []
        for file in self._catalog.get_files_from_record(record, limit):
            transfers += self._move_record_entry(
                record.id, file, qos, move_function, register, check_exists, dry
            )
        print(f"{len(transfers)} transfers have been issued")
        return transfers

    def doOperation(self, operation, record_uuid, limit, register, check_exists, dry):
        """Internal function."""
        if operation == "archive":
            return self._move_record(
                record_uuid,
                limit,
                "cold",
                self._storage.archive,
                register,
                check_exists,
                dry,
            )
        elif operation == "stage":
            return self._move_record(
                record_uuid,
                limit,
                "hot",
                self._storage.stage,
                register,
                check_exists,
                dry,
            )
        elif operation == "clear_hot":
            return self.clear_hot(record_uuid, limit, dry)
        raise ValueError(
            f"The cold manager does not understand the operation '{operation}'"
        )

    def clear_hot(self, record_uuid, limit, dry):
        """Remove the hot copy of a file that has a copy on cold storage."""
        # Let's find the files inside the record
        cleared = False
        record = self._catalog.get_record(record_uuid)
        if not record:
            return []
        for file in self._catalog.get_files_from_record(record, limit):
            if not self._is_qos(file, "cold"):
                print(
                    "I don't want to remove the hot copy, since the cold does not exist!"
                )
                continue
            print(" the file is cold and ", end="")
            if not self._is_qos(file, "hot"):
                print("the file is not in hot. Ignoring it")
                continue
            print(f"ready to be deleted")
            if not dry:
                self._storage.clear_hot(file["uri"])
            else:
                print("Dry run: do not remove the file (but cleaning the repository)")
            self._catalog.clear_hot(record, file["file_id"])
            cleared = True
        self._catalog.reindex_entries()
        return [cleared]

    def check_current_transfers(self):
        """Check the transfers that are ongoing."""
        print("Checking all the ongoing transfers")
        now = datetime.utcnow()
        all_status = {}
        summary = {}
        for transfer in Transfer.get_ongoing_transfers(now):
            id = transfer.id
            transfer.last_check = datetime.utcnow()
            print(f"Transfer {id}:", end="")
            transfer.status, error = self._storage._transfers[
                transfer.method
            ].transfer_status(transfer.method_id)
            all_status[id] = transfer.status
            if transfer.status not in summary:
                summary[transfer.status] = 0
            summary[transfer.status] += 1
            if transfer.status == "DONE":
                print(" just finished! Let's update the catalog and mark it as done")
                transfer.finished = datetime.now()
                self._catalog.add_copy(
                    transfer.record_uuid,
                    transfer.file_id,
                    transfer.new_qos,
                    transfer.new_filename,
                )
            if transfer.status == "FAILED" or not transfer.status:
                print("The transfer failed :(")
                transfer.reason = error
                transfer.finished = datetime.now()
            else:
                print(f" status {transfer.status}")
            db.session.add(transfer)
            db.session.commit()
        self._catalog.reindex_entries()
        print("Summary: ", summary)
        return all_status

    def settings(self):
        """Return the configuration of the cold_storage."""
        return "Storing settings: " + self._storage.settings()

    def list(self, record_id):
        """Returns the location of the files for a particular record."""
        record = self._catalog.get_record(record_id)
        return self._catalog.get_files_from_record(record)

    def check_requests(self):
        """Check all the requests for staging data."""
        TransferRequest.process_submitted_transfers(self)

        # Now, let's look at the ones that 'started'
        TransferRequest.process_running_transfers()

        # Now, the request to archive
        TransferRequest.process_archiving_transfers()

        # Finally, the ones that are waiting to be archive
        TransferRequest.process_to_archive_transfers(self)
