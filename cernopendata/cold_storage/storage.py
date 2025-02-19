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
import os
import re

from pkg_resources import iter_entry_points

from .transfer.cp import TransferManager as CPManager
from .transfer.fts import TransferManager as FTSManager


def default_transfer():
    """Default Transfer Manager."""
    return TransferManager()


def default_cold_path():
    """Default Path for cold data."""
    return "var/data_cold"


def default_hot_path():
    """Default path for hot data."""
    return "var/data"


class Storage:
    """Class to deal with the storage of the files."""

    def __init__(self, app=None):
        """Initializing the class."""
        if False:  # app:
            self._hot_path = []
            for entry_point in iter_entry_points(
                "cernopendata.cold_storage.storage", name="hot_path"
            ):
                self._hot_path.append(entry_point.load()())
            self._cold_path = []
            for entry_point in iter_entry_points(
                "cernopendata.cold_storage.storage", name="cold_path"
            ):
                self._cold_path.append(entry_point.load()())
            self._transfer = []
            for entry_point in iter_entry_points(
                "cernopendata.cold_storage.storage", name="transfer"
            ):
                self._transfer.append(entry_point.load()())
        else:
            self._cold_path = [
                "/opt/invenio/var/instance/data_cold/",
                "https://eosctapublic.cern.ch:8444/eos/ctapublic/archive/opendata/atlas",
                "https://eosctapublic.cern.ch:8444/eos/ctapublic/archive/opendata/cms",
                "https://eosctapublic.cern.ch:8444/eos/ctapublic/archive/opendata/lhcb",
            ]
            self._transfer = [CPManager(), FTSManager(), FTSManager(), FTSManager()]
            self._hot_path = [
                "/home/invenio/hot_cache",
                "root://eospublic.cern.ch//eos/opendata/atlas",
                "root://eospublic.cern.ch//eos/opendata/cms",
                "root://eospublic.cern.ch//eos/opendata/lhcb",
            ]
            self._transfers = {}
            # Let's make a dictionary of the possible transfers. This is used to query the status later on
            for t in self._transfer:
                self._transfers[t.__class__.__module__] = t

    def find_cold_url(self, file):
        """Identify the URL that a given file should have."""
        i = 0
        for prefix in self._hot_path:
            if prefix in file:
                return file.replace(prefix, self._cold_path[i]), self._transfer[i]
            i += 1
        return None, None

    def archive(self, file):
        """Create a cold copy for a file."""
        print(f"Archiving it")
        filename = file["uri"]
        # print(f"SWAPPING {self._hot_path[0]} by {self._cold_path[0]}")
        dest_file, transfer = self.find_cold_url(filename)
        if not dest_file:
            print(f"WE CAN'T GUESS THE destination path :( of {filename}")
            return []
        id = transfer.archive(filename.replace("root://", "https://"), dest_file)
        if not id:
            print("Error creating the transfer")
            return []
        return {
            "id": id,
            "new_qos": "cold",
            "new_filename": dest_file,
            "filename": filename,
            "transfer": transfer.__class__.__module__,
        }

    def stage(self, file):
        """Create a hot copy for a file."""
        filename = file["tags"]["uri_cold"]
        dest_file, transfer = self.find_hot_url(
            filename
        )  # filename.replace(self._cold_path[0], self._hot_path[0])
        print(f" Staging it")
        id = transfer.stage(filename, dest_file)
        if not id:
            print("Error creating the transfer")
            return []
        return {
            "id": id,
            "new_qos": "hot",
            "new_filename": dest_file,
            "filename": filename,
        }

    def clear_hot(self, filename):
        """Clear the hot copy of a file."""
        # print(f"Ready to delete {filename}")
        try:
            os.remove(re.sub("^file://[^/]*/", "/", filename))
        except Exception as e:
            print(f"Error deleting the file {filename} :*(", e)

    def settings(self):
        """Return the settings of the storage."""
        return (
            f"Storing hot in {self._hot_path}, cold in {self._cold_path} using "
            + "{self._transfer} to transfer the files"
        )
