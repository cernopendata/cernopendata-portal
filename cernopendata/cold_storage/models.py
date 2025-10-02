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

"""Cold Storage Transfer requests."""
from datetime import datetime

from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy_utils.types import UUIDType


class RequestMetadata(db.Model):
    """Class to store the requests that users have made to request files that are available on cold storage."""

    __tablename__ = "cold_requests_metadata"
    __table_args__ = (
        db.Index("ix_cold_requests_action", "action"),
        db.Index("ix_cold_requests_status", "status"),
        db.Index("ix_cold_requests_completed_at", "completed_at"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    action = db.Column(db.String(50), default="stage", nullable=False)
    status = db.Column(db.String(50), default="submitted", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    num_files = db.Column(db.Integer, default=0, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    subscribers = db.Column(MutableList.as_mutable(JSONB), default=list)
    size = db.Column(db.BigInteger, default=0, nullable=True)
    file = db.Column(db.String(255), nullable=True)
    num_hot_files = db.Column(db.Integer, nullable=True)
    num_cold_files = db.Column(db.Integer, nullable=True)


class Location(db.Model):
    """Class for the settings."""

    __tablename__ = "cold_location"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    cold_path = db.Column(db.String(512), nullable=False)
    hot_path = db.Column(db.String(512), nullable=False, unique=True)
    manager_class = db.Column(db.String(512), nullable=False)


class TransferMetadata(db.Model):
    """Class for a transfer."""

    __tablename__ = "cold_transfers_metadata"

    __table_args__ = (
        db.Index("ix_cold_transfers_record", "record_uuid"),
        db.Index("ix_cold_transfers_last_check", "last_check"),
        db.Index("ix_cold_transfers_status", "status"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_uuid = db.Column(db.String(36), nullable=False)
    file_id = db.Column(db.String(36), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    new_filename = db.Column(db.String(512), nullable=False)
    method = db.Column(db.String(512), nullable=False)
    method_id = db.Column(db.String(36), nullable=False)
    submitted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_check = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    size = db.Column(db.BigInteger, default=0, nullable=True)
    """Size of file."""
