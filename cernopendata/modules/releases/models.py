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

"""CERN Open Data Release models."""

from enum import Enum

from invenio_db import db
from sqlalchemy.dialects.postgresql import JSONB


class ReleaseStatus(Enum):
    """Possible Status for a release."""

    DRAFT = "DRAFT"
    READY = "READY"
    EDITING = "EDITING"
    STAGED = "STAGED"
    STAGING = "STAGING"
    PUBLISHED = "PUBLISHED"


class ReleaseValidationMetadata(db.Model):
    """Validation results for a release."""

    __tablename__ = "releases_validations"

    id = db.Column(db.Integer, primary_key=True)

    release_id = db.Column(
        db.Integer,
        db.ForeignKey("releases_metadata.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    release = db.relationship(
        "ReleaseMetadata",
        back_populates="validations",
    )

    enabled = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint("release_id", "name", name="uq_release_validation"),
    )


class ReleaseHistory(db.Model):
    """History of a release."""

    __tablename__ = "releases_history"

    id = db.Column(db.Integer, primary_key=True)

    release_id = db.Column(
        db.Integer, db.ForeignKey("releases_metadata.id"), nullable=False
    )

    status = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("accounts_user.id"))

    release = db.relationship("ReleaseMetadata", back_populates="history_events")
    user = db.relationship("User")


class ReleaseMetadata(db.Model):
    """Release model."""

    __tablename__ = "releases_metadata"

    BULK_IMMUTABLE_FIELDS = ["recid", "title", "DOI"]
    status = db.Column(
        db.String(20),
        nullable=False,
        index=True,
    )

    # --- Identifiers ---
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    discussion_url = db.Column(
        db.String(2048),
        nullable=True,
    )

    history_events = db.relationship(
        "ReleaseHistory",
        back_populates="release",
        order_by="ReleaseHistory.timestamp",
        cascade="all, delete-orphan",
    )

    experiment = db.Column(db.String(50), nullable=False)

    # --- Content ---
    json_fields = ["records", "documents", "glossary", "errors"]
    for f in json_fields:
        default = list if f == "errors" else dict
        locals()[f] = db.Column(JSONB, nullable=False, default=default)

    # --- Counters ---
    int_fields = [
        "num_records",
        "num_errors",
        "num_docs",
        "num_files",
        "num_file_indices",
    ]
    for f in int_fields:
        locals()[f] = db.Column(db.Integer, nullable=False, default=0)

    size_files = db.Column(
        db.BigInteger,
        nullable=False,
        default=0,
    )

    size_indexFiles = db.Column(
        db.BigInteger,
        nullable=False,
        default=0,
    )

    # --- Validation flags ---
    validations = db.relationship(
        "ReleaseValidationMetadata",
        back_populates="release",
        cascade="all, delete-orphan",
    )

    max_recid = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )
