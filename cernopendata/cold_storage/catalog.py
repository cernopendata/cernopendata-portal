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

"""Cold Storage Catalog."""

from datetime import datetime

from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion, ObjectVersionTag
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.api import RecordFilesWithIndex


class Catalog:
    """Class to interact with the repository."""

    def __init__(self, debug=False):
        """Initialize the catalog."""
        self._indexer = RecordIndexer()
        self._debug = debug
        self._reindex_queue = []

    def get_record(self, record_uuid):
        """First, lets get the record."""
        try:
            record = RecordFilesWithIndex.get_record(record_uuid)
        except Exception as e:
            print(f"Couldn't find a record  with the id '{record_uuid}': {e}")
            return
        return record

    def get_files_from_record(self, record, limit=None):
        """Getting the files from a record."""
        files = []
        if self._debug:
            print("DEBUG: The catalog got the record:", record.to_dict())
        if record:
            if "_files" in record:
                files += record["_files"]
            if "_file_indices" in record:
                for f in record["_file_indices"]:
                    files += f["files"]
        if limit:
            start = 0
            end = len(files)
            if limit < 0:
                start = -limit
            else:
                end = limit
            files = files[start:end]
        if self._debug:
            print("DEBUG: And the list of files are:", files)
        return files

    def clear_hot(self, record, file_id):
        """Marking the hot copy as deleted."""

        def _clear_hot_function(version_id):
            """Create a tag for the file identifying that the copy is not available."""
            ObjectVersionTag.create(version_id, "hot_deleted", str(datetime.now()))

        return self._update_file_and_reindex(record.id, file_id, _clear_hot_function)

    def _update_file_and_reindex(self, record_uuid, file_id, update_function):
        """Function to update the repository."""
        f = FileInstance.get(file_id)
        if not f:
            print(f"Can't find that file :( {file_id}")
            return False
        objectVersion = ObjectVersion.query.filter_by(file_id=f.id).one_or_none()
        if not objectVersion:
            print(f"Can't find the object associated to that file :( {file_id}")
            return False
        update_function(objectVersion.version_id)
        db.session.commit()
        if record_uuid not in self._reindex_queue:
            print(f"Record {record_uuid} will be reindexed")
            self._reindex_queue += [record_uuid]
        return True

    def reindex_entries(self):
        """Reindexes all the entries that have been modified."""
        while len(self._reindex_queue) > 0:
            record_uuid = self._reindex_queue.pop(0)
            print(f"Ready to reindex {record_uuid}")
            record = RecordFilesWithIndex.get_record(record_uuid)
            if not record:
                print(f"Couldn't find that record '{record_uuid}'")
                continue
            print("Got the object from the database")
            record.files.flush()
            record.flush_indices()
            record.commit()
            db.session.commit()
            try:
                self._indexer.index(record)
            except Exception as e:
                print(f"Error during the reindex {e}")
                try:
                    record.commit()
                    self._indexer.index(record)
                    print("The second time worked!")
                except Exception as e:
                    print(f"Doing it again did not help :( {e}")

    def add_copy(self, record_uuid, file_id, new_qos, new_filename):
        """Adds a copy to a particular file. It reindexes the record."""

        def _add_copy_function(version_id):
            """Function to add a file tag with a new uri for the file."""
            if new_qos == "cold":
                ObjectVersionTag.create_or_update(version_id, "uri_cold", new_filename)
            elif new_qos == "hot":
                ObjectVersionTag.delete(version_id, "hot_deleted")

        return self._update_file_and_reindex(record_uuid, file_id, _add_copy_function)
