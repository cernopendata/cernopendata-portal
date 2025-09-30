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

"""Schemas used for the transfers."""
from marshmallow import Schema, fields, validate


class TransferRequestQuerySchema(Schema):
    """Arguments for the transfer search."""

    page = fields.Int(missing=1)
    per_page = fields.Int(missing=10)
    status = fields.List(fields.Str())
    action = fields.List(fields.Str())
    record = fields.Str()
    sort = fields.Str()
    direction = fields.Str(validate=validate.OneOf(["asc", "desc"]), load_default="asc")


class TransferRequestSchema(Schema):
    """Schema of a transfer."""

    id = fields.Str()
    recid = fields.Method("get_recid")
    action = fields.Str()
    num_files = fields.Int()
    size = fields.Int()
    status = fields.Str()
    created_at = fields.DateTime()
    started_at = fields.DateTime(allow_none=True)
    completed_at = fields.DateTime(allow_none=True)
    num_hot_files = fields.Int()
    num_cold_files = fields.Int()
    num_record_files = fields.Method("get_num_record_files")
    record_size = fields.Method("get_record_size")

    def get_recid(self, obj):
        """Convert the uuid into the recid."""
        pid_mappings = self.context.get("pid_mappings", {})
        recid = pid_mappings.get(obj.record_id)
        return recid if recid else None

    def get_num_record_files(self, obj):
        """Get the number of files from the record data."""
        record_data = self.context.get("records_data", {}).get(str(obj.record_id))
        if record_data and record_data.get("distribution"):
            return record_data["distribution"].get("number_files")
        return None

    def get_record_size(self, obj):
        """Get the size of the files from the record data."""
        record_data = self.context.get("records_data", {}).get(str(obj.record_id))
        if record_data and record_data.get("distribution"):
            return record_data["distribution"].get("size")
        return None
