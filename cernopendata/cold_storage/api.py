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

"""Cold Storage API."""

import importlib
import logging
from datetime import datetime
from enum import Enum

from flask import current_app
from flask_mail import Message
from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion, ObjectVersionTag
from invenio_records_files.api import FileObject, Record
from sqlalchemy import func

from .models import RequestMetadata, TransferMetadata

logger = logging.getLogger(__name__)


class ColdStorageActions(Enum):
    """Possible cold storage actions."""

    STAGE = "stage"
    ARCHIVE = "archive"
    CLEAR_HOT = "clear_hot"


class FileAvailability(Enum):
    """Define the possible availabilities for a single file."""

    ONLINE = "online"
    ONDEMAND = "on demand"


class RecordAvailability(Enum):
    """Define the possible availabilities for a record."""

    ONLINE = "online"
    ONDEMAND = "on demand"
    PARTIAL = "partial"
    REQUESTED = "requested"


class FileObjectCold(FileObject):
    """Overwrite the fileobject to get multiple URI."""

    @classmethod
    def create(self, bucket, filename, file_id):
        """Create a cold file object."""
        return ObjectVersion.create(bucket, filename, file_id)

    def dumps(self):
        """This one has the information about the cold URI stored in a ObjectVersionTag."""
        info = super(FileObjectCold, self).dumps()
        info["tags"] = {}
        for tagName in ("uri_cold", "hot_deleted"):
            tag = ObjectVersionTag.get(str(self.obj.version_id), tagName)
            if tag:
                info["tags"][tagName] = tag.value
        info["availability"] = self.availability
        if "uri" not in info:
            file = FileInstance.get(str(self.obj.file_id))
            info["uri"] = file.uri
        return info

    @property
    def availability(self):
        """Describe the QoS of the file."""
        if "availability" not in self.data:
            avl = FileAvailability.ONLINE
            for t in self.obj.tags:
                if t.key == "hot_deleted":
                    avl = FileAvailability.ONDEMAND
            self.data["availability"] = avl.value
        return self.data["availability"]


class Transfer:
    """API for managing cold storage transfers."""

    @staticmethod
    def create(entry):
        """Create a new transfer entry."""
        transfer = TransferMetadata(
            action=entry["action"],
            new_filename=entry["new_filename"],
            record_uuid=entry["record_uuid"],
            file_id=entry["file_id"],
            method=entry["method"],
            method_id=entry.get("method_id", ""),
            submitted=datetime.utcnow(),
            last_check=datetime.utcnow(),
            size=entry.get("size", None),
        )
        db.session.add(transfer)
        db.session.commit()
        return transfer

    @staticmethod
    def get_ongoing_transfers(last_check):
        """Get transfers that need processing."""
        return (
            TransferMetadata.query.filter(
                TransferMetadata.last_check <= last_check,
                TransferMetadata.finished.is_(None),
            )
            .order_by(TransferMetadata.last_check)
            .all()
        )

    @staticmethod
    def is_scheduled(file_id, action):
        """Check if a transfer is already scheduled."""
        return (
            db.session.query(TransferMetadata.id)
            .filter(
                TransferMetadata.action == action.value,
                TransferMetadata.file_id == file_id,
                TransferMetadata.finished.is_(None),
            )
            .first()
            is not None
        )

    @staticmethod
    def load_class(full_class_path):
        """Load a class given a python path."""
        module_path, class_name = full_class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls()

    @staticmethod
    def get_active_transfers_threshold(action):
        """Get the maximum number of active transfers."""
        if action == ColdStorageActions.STAGE:
            return current_app.config["COLD_ACTIVE_STAGING_TRANSFERS_THRESHOLD"]
        if action == ColdStorageActions.ARCHIVE:
            return current_app.config["COLD_ACTIVE_ARCHIVING_TRANSFERS_THRESHOLD"]


class Request:
    """Class to check the cold storage requests."""

    @staticmethod
    def send_email(req, emails):
        """Send an email notification using Invenio's mail system."""
        subject = f"Transfer {req.id} Completed"
        body = f"Hello,\n\nYour transfer with ID {req.id} has been completed successfully.\n\nBest regards."
        msg = Message(
            subject, sender="opendata-noreply@cern.ch", recipients=emails, body=body
        )
        # Use InvenioMail's send_email function with a simple text template
        try:
            current_app.extensions["mail"].send(msg)
            logger.info(f"Email sent to {emails}")
        except Exception as e:
            logger.error(f"Failed to send email to {emails}: {e}")

    @staticmethod
    def create(
        record_id, subscribers=None, file=None, availability=None, distribution=None
    ):
        """Create a new request."""
        rb = RequestMetadata(
            record_id=record_id, file=file, subscribers=subscribers or []
        )
        if availability:
            rb.num_hot_files = availability.get("online")
            rb.num_cold_files = availability.get("on demand")
        if distribution:
            rb.num_record_files = distribution.get("number_files")
            rb.record_size = distribution.get("size")
        db.session.add(rb)
        return rb

    @staticmethod
    def mark_as_started(req, num_files, size):
        """Mark a request as started."""
        logger.info(f"The transfer {req.id} has started")
        req.started_at = datetime.utcnow()
        req.status = "started"
        req.num_files = num_files
        req.size = size
        db.session.add(req)

    @staticmethod
    def mark_as_completed(req):
        """Mark the request as DONE and notify subscribers."""
        req.status = "completed"
        req.completed_at = datetime.utcnow()
        db.session.add(req)
        if req.subscribers:
            print("Sending emails")
            # Notify subscribers
            Request.send_email(req, req.subscribers)
        db.session.commit()
        return True

    @staticmethod
    def subscribe(transfer_id, email):
        """Add an email to the subscribers of a transfer."""
        transfer = RequestMetadata.query.filter_by(id=transfer_id).first()

        if email not in transfer.subscribers:
            transfer.subscribers.append(email)
            db.session.add(transfer)
            db.session.commit()
            return True
        return False


class ColdRecord(Record):
    """Extends the record class to have the calculation of the availability."""

    def check_availability(self):
        """Calculate the availability of the record based on the files and file indices."""
        self._avl = {}

        for index in self.file_indices:
            # And let's propagate the availability to the record
            for avl in index["availability"]:
                if avl not in self._avl:
                    self._avl[avl] = 0
                self._avl[avl] += index["availability"][avl]
        for file in self.files:
            avl = file["availability"]
            if avl not in self._avl:
                self._avl[avl] = 0
            self._avl[avl] += 1
        self["_availability_details"] = self._avl
        if len(self._avl.keys()) == 0:
            self["availability"] = RecordAvailability.ONLINE.value
        elif len(self._avl.keys()) == 1:
            self["availability"] = list(self._avl.keys())[0]
        else:
            self["availability"] = RecordAvailability.PARTIAL.value

        count_requests = (
            db.session.query(func.count())
            .filter(
                RequestMetadata.record_id == str(self.id),
                RequestMetadata.status == "submitted",
                RequestMetadata.action == ColdStorageActions.STAGE.value,
            )
            .scalar()
        )
        count_transfers = (
            db.session.query(func.count())
            .filter(
                TransferMetadata.record_uuid == str(self.id),
                TransferMetadata.finished.is_(None),
                TransferMetadata.action == ColdStorageActions.STAGE.value,
            )
            .scalar()
        )
        # If there are staging requests or transfers that have not finished, it should be in requested
        if count_requests or count_transfers:
            self["availability"] = RecordAvailability.REQUESTED.value
