# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017-2026 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""Base class for all the cern open data entries."""
from invenio_records import Record

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sqlalchemy import cast, Integer, func


class OpenDataRecord(Record):
    """Base class for all the cern open data entries."""

    @classmethod
    def create(cls, data, id_field, id_=None, **kwargs):
        """Create a new record. It adds versions and the field that it is used for the id."""
        if "_concept_parent" not in data:
            data["_concept_parent"] = data[id_field]

        if "version" not in data:
            data["version"] = 1

        if "_versions" not in data:
            data["_versions"] = {}

        data["_id_field"] = id_field
        data["_versions"].setdefault("index", data["version"])
        data["_versions"].setdefault("is_latest", True)
        print("IN THE OPENDATARECORD")
        recid = data.get("recid")
        if recid and recid.isdigit():
            experiment = data.get("experiment")[0]
            recid = f"{experiment}-{recid}".lower()
            data["recid"] = recid
        return super().create(data, id_=id_, **kwargs)

    @property
    def concept_parent(self):
        """Value of the concept record. This is the meta record, pointing to the latest version."""
        return self.get("_concept_parent")

    @property
    def version_index(self):
        """Return the current version."""
        return self.get("_versions", {}).get("index", 1)

    @property
    def is_latest(self):
        """Return a boolean specifying if this is the latest record."""
        return self.get("_versions", {}).get("is_latest", True)

    @property
    def pid_value(self):
        """Return the identifier of the record and version."""
        return f"{self[self['_id_field']]}-v{self.version_index}"

    @classmethod
    def get_latest_version(cls, recid):
        """Get the latest version of the record, or 0 if it does not exist."""
        latest = (
            PersistentIdentifier.query.filter(
                PersistentIdentifier.pid_value.like(f"{recid}-v%")
            )
            .with_entities(
                func.max(
                    cast(
                        func.substring(PersistentIdentifier.pid_value, r"-v([0-9]+)$"),
                        Integer,
                    )
                )
            )
            .scalar()
        ) or 0

        return latest
