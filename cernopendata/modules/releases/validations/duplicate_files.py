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
"""Validation process."""
from invenio_files_rest.models import FileInstance

from .base import Validation
from cernopendata.api import RecordFilesWithIndex


class CheckDuplicateFiles(Validation):
    """Validation to check for duplicate files."""

    name = "Duplicate files"
    error_message = "Some of the files of the records are already registered"

    def validate(self, release):
        """Check that URIs in this release are not already persisted in the system."""
        errors = []
        for record in release.records:
            for f in record.get("files", []):
                # We should check that the file is not there for other recid
                error = self._file_already_used(f["uri"], record["recid"])
                if error:
                    errors.append(error)
        return errors

    def _file_already_used(self, uri, recid):
        """Check if a particular file is used by a different record."""
        existing_recid = RecordFilesWithIndex.get_record_for_file(uri)
        if existing_recid and existing_recid != recid:
            return f"The file {uri} is already used by a different record: {recid} (instead of {existing_recid})"
        return None
