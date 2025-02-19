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

from flask import current_app
from invenio_db import db
from invenio_mail import InvenioMail
from invenio_records.models import RecordMetadata
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy_utils.types import UUIDType

from cernopendata.api import RecordFilesWithIndex


class TransferRequest(db.Model):
    """Class to store the requests that users have made to request files that are available on cold storage."""

    __tablename__ = "cold_requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    status = db.Column(db.String(50), default="submitted", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    num_files = db.Column(db.Integer, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cleaned_at = db.Column(db.DateTime, nullable=True)
    subscribers = db.Column(
        MutableList.as_mutable(JSONB), default=list
    )  # <--- Use MutableList

    def save(self):
        """Save the transfer request to the database."""
        db.session.add(self)
        db.session.commit()

    def _send_email(self, email):
        """Send an email notification using Invenio's mail system."""
        subject = f"Transfer {self.id} Completed"
        body = f"Hello,\n\nYour transfer with ID {self.id} has been completed successfully.\n\nBest regards."

        # Use InvenioMail's send_email function with a simple text template
        try:
            current_app.extensions["mail"].send(
                body=body,
                subject=subject,
                recipients=[email],
                context={"id": self.id, "status": "completed"},
            )
            print(f"Email sent to {email}")
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

    @classmethod
    def create_transfer(cls, record_id, subscribers):
        """Create a new transfer document in OpenSearch."""
        rb = cls()
        rb.record_id = record_id
        rb.subscribers = subscribers if subscribers else []

        rb.save()
        return rb

    def start_transfer(self, num_files):
        """Mark a transfer as started."""
        print(f"The transfer {self.id} has started")
        self.started_at = datetime.utcnow()
        self.status = "started"
        self.num_files = num_files

        self.save()

    def complete_transfer(self):
        """Mark the transfer as DONE and notify subscribers."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.save()

        # Notify subscribers
        for email in self.subscribers:
            self._send_email(email)

        return True

    def subscribeToTransfer(self, email):
        """Add an email to the subscribers of a transfer."""
        if email not in self.subscribers:
            self.subscribers.append(email)
            self.save()
            return f"{email} subscribed successfully", 200
        return f"{email} is already subscribed", 403

    @classmethod
    def process_running_transfers(cls):
        """Find all running transfers and complete them."""
        transfers = cls.query.filter_by(status="started").all()
        for transfer in transfers:
            record = RecordFilesWithIndex.get_record(transfer.record_id)
            if record["availability"] == "online":
                transfer.complete_transfer()

    @classmethod
    def process_submitted_transfers(cls, manager):
        """Check if there are any new transfers submitted."""
        transfers = cls.query.filter_by(status="submitted").all()
        for transfer in transfers:
            info = manager.doOperation(
                "stage",
                transfer.record_id,
                limit=None,
                register=True,
                check_exists=True,
                dry=True,
            )
            transfer.start_transfer(len(info))


class Transfer(db.Model):
    """Class for a transfer."""

    __tablename__ = "cold_transfers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_uuid = db.Column(db.String(36), nullable=False)
    file_id = db.Column(db.String(36), nullable=False)
    new_qos = db.Column(db.String(50), nullable=False)
    new_filename = db.Column(db.String(255), nullable=False)
    method = db.Column(db.JSON, nullable=False)
    submitted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_check = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished = db.Column(db.DateTime, nullable=True)  # Acknowledgment timestamp
    status = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.Text, nullable=True)

    @classmethod
    def create_transfer(cls, entry):
        """Create a new transfer entry."""
        transfer = cls(
            new_qos=entry["new_qos"],
            new_filename=entry["new_filename"],
            record_uuid=entry["record_uuid"],
            file_id=entry["file_id"],
            method=entry["method"],
            submitted=datetime.utcnow(),
            last_check=datetime.utcnow(),
        )
        db.session.add(transfer)
        db.session.commit()
        return transfer.id

    #    @classmethod
    #    def update_transfer(cls, id, status, finished, reason=None):
    #        """Update a transfer's status and timestamps."""
    #        transfer = cls.query.get(id)
    #        if transfer:
    #            transfer.status = status
    #            transfer.last_check = datetime.utcnow()
    #            if finished:
    #                transfer.ack = datetime.utcnow()
    #            if reason:
    #                transfer.reason = reason
    #            db.session.commit()

    @classmethod
    def get_ongoing_transfers(cls, last_check):
        """Get transfers that need processing."""
        return (
            cls.query.filter(cls.last_check <= last_check, cls.finished.is_(None))
            .order_by(cls.last_check)
            .all()
        )

    #    @classmethod
    #    def get_transfer_details(cls, id):
    #        """Get details of a specific transfer."""
    #        return cls.query.get(id)

    @classmethod
    def is_scheduled(cls, file_id, qos):
        """Check if a transfer is scheduled."""
        return (
            db.session.query(cls.id)
            .filter(cls.new_qos == qos, cls.file_id == file_id, cls.finished.is_(None))
            .first()
            is not None
        )
