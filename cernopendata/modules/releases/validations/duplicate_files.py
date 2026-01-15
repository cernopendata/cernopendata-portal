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

from ..models import ReleaseStatus
from .base import Validation


class CheckDuplicateFiles(Validation):
    """Validation to check for duplicate files."""

    name = "Duplicate files"
    error_message = "Some of the files of the records are already registered"

    def validate(self, release):
        """Check that URIs in this release are not already persisted in the system."""
        errors = []
        if not self._metadata.status or self._metadata.status in [
            ReleaseStatus.DRAFT.value,
            ReleaseStatus.READY.value,
            ReleaseStatus.EDITING.value,
        ]:
            uris = {
                f["uri"]
                for record in self._metadata.records
                for f in record.get("files", [])
                if "uri" in f
            }

            if uris:
                # Query ObjectVersion for existing URIs
                existing_files = FileInstance.query.filter(
                    FileInstance.uri.in_(uris)
                ).all()

                # Collect colliding URIs
                used_uris = {obj.uri for obj in existing_files}

                if used_uris:
                    errors.append(
                        f"The following file URIs are already stored in the system: "
                        f"{', '.join(sorted(used_uris))}"
                    )
        return errors
