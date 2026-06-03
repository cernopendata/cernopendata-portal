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

"""API for CERN Open Data records."""

from invenio_records import Record


class OpenDataRecord(Record):
    """Base class for all the cern open data entries."""

    @classmethod
    def create(cls, data, id_field, id_=None, **kwargs):
        """Create a new record. It adds versions and the field that it is used for the id."""
        if "_conceptrecid" not in data:
            data["_conceptrecid"] = data[id_field]

        if "_versions" not in data:
            data["_versions"] = {}

        data["_id_field"] = id_field
        data["_versions"].setdefault("index", 1)
        data["_versions"].setdefault("is_latest", True)
        data["_versions"].setdefault("latest_index", data["_versions"]["index"])

        return super().create(data, id_=id_, **kwargs)

    @property
    def conceptrecid(self):
        """Value of the concept record. This is the meta record, pointing to the latest version."""
        return self.get("_conceptrecid")

    @property
    def version_index(self):
        """Return the current version."""
        return self.get("_versions", {}).get("index", 1)

    @property
    def is_latest(self):
        """Return a boolean specifying if this is the latest record."""
        return self.get("_versions", {}).get("is_latest", True)

    @property
    def latest_index(self):
        """Return the index of the latest version of this entry."""
        return self.get("_versions", {}).get("latest_index", self.version_index)

    @property
    def pid_value(self):
        """Return the identifier of the record and version."""
        return f"{self[self['_id_field']]}-v{self.version_index}"
