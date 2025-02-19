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
"""Service for the Cold Storage."""

import logging
from datetime import datetime

from flask import current_app
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy import func

from cernopendata.api import RecordFilesWithIndex

from .api import FileAvailability, RecordAvailability, Request, Transfer
from .catalog import Catalog
from .manager import ColdStorageManager
from .models import RequestMetadata, TransferMetadata

logger = logging.getLogger(__name__)


class TransferService:
    """Service to handle the transfers."""

    @staticmethod
    def process_transfers():
        """Check all the ongoing transfers."""
        logger.info("Checking all the ongoing transfers")
        catalog = Catalog()
        now = datetime.utcnow()
        all_status = {}
        summary = {}
        for transfer in Transfer.get_ongoing_transfers(now):
            id = transfer.id
            transfer.last_check = datetime.utcnow()
            transfer.status, error = Transfer.load_class(
                f"{transfer.method}.TransferManager"
            ).transfer_status(transfer.method_id)
            all_status[id] = transfer.status
            if transfer.status not in summary:
                summary[transfer.status] = 0
            summary[transfer.status] += 1
            if transfer.status == "DONE":
                logger.debug(
                    f"Transfer {id}: just finished! Let's update the catalog and mark it as done"
                )
                transfer.finished = datetime.now()
                catalog.add_copy(
                    transfer.record_uuid,
                    transfer.file_id,
                    transfer.action,
                    transfer.new_filename,
                )
            if transfer.status == "FAILED" or not transfer.status:
                logger.error(f"The transfer {id} failed :(")
                transfer.reason = error
                transfer.finished = datetime.now()
            else:
                logger.debug(f"Transfer {id} is in status {transfer.status}")
            db.session.add(transfer)
            db.session.commit()
        catalog.reindex_entries()
        logger.info(f"Summary: {summary}")
        return all_status


class RequestService:
    """Service to handle the requests."""

    @staticmethod
    def process_requests():
        """Check the active requests."""
        # The requests would go through these stages
        # SUBMITTED ->  STARTED -> COMPLETED
        RequestService.check_submitted()

        # Now, let's look at the ones that 'started'
        RequestService.check_running()

    @staticmethod
    def check_submitted():
        """Check if there are any new transfers submitted."""
        manager = ColdStorageManager()
        for action_enum in ColdStorageActions:
            action = action_enum.value
            active_transfers_count = TransferMetadata.query.filter(
                TransferMetadata.finished.is_(None), TransferMetadata.action == action
            ).count()
            threshold = Transfer.get_active_transfers_threshold(action_enum)

            logger.info(
                f"Checking if we can {action} more records: active {active_transfers_count}/{threshold}"
            )
            submitted = 0
            limit = threshold - active_transfers_count
            if limit > 0:
                transfers = RequestMetadata.query.filter_by(
                    status="submitted", action=action
                ).all()

                for transfer in transfers:
                    info = manager.doOperation(
                        action,
                        transfer.record_id,
                        limit=limit,
                        register=True,
                        force=False,
                        dry=False,
                    )
                    logger.debug(f"Got {info}")
                    if info:
                        submitted += len(info)
                        transfer.num_files += len(info)
                        transfer.size += sum(item.size for item in info)
                    transfer.started_at = datetime.utcnow()
                    logger.info(f"THE LIMIT WAS {limit}, AND WE SUBMITTED {submitted}")
                    if limit == submitted:
                        logger.info(
                            f"Reached the threshold of {threshold} transfers. There might be more in this record"
                            f"({submitted + active_transfers_count}). Let's wait before continuing"
                        )
                    else:
                        transfer.status = "started"
                    db.session.add(transfer)
                    limit -= submitted
                    if limit <= 0:
                        logger.info("We have submitted enough. Stopping")
                        break
            if submitted:
                logger.info(f"{submitted} transfers have been submitted!")
            db.session.commit()

    @staticmethod
    def check_running():
        """Check the records that are being archived."""
        for action_enum in ColdStorageManager:
            action = action_enum.value

            requests = RequestMetadata.query.filter_by(
                status="started", action=action
            ).all()
            logger.debug(f"Checking the {len(requests)} {action} requests")
            completed = 0
            for request in requests:
                record = RecordFilesWithIndex.get_record(request.record_id)

                if action == "stage":
                    if record["availability"] != RecordAvailability.ONLINE.value:
                        continue
                elif action == "archive":
                    files = (f for index in record.file_indices for f in index["files"])
                    missing = next(
                        (
                            f
                            for f in files
                            if "tags" not in f or "uri_cold" not in f["tags"]
                        ),
                        None,
                    )
                    if missing:
                        logger.debug(f"The file {missing['key']} is not in tape yet...")
                        continue
                completed += 1
                Request.mark_as_completed(request)
            logger.info(f"{completed}/{len(requests)} requests have finished")

    @staticmethod
    def get_requests(
        status=None,
        action=None,
        record=None,
        summary=False,
        sort=None,
        direction=None,
        page=None,
        per_page=None,
    ):
        """Get the summary of the requests."""
        if summary:
            query = db.session.query(
                RequestMetadata.status,
                RequestMetadata.action,
                func.count().label("count"),
                func.sum(RequestMetadata.num_files).label("files"),
                func.sum(RequestMetadata.size).label("size"),
            )
        else:
            query = RequestMetadata.query

        if status:
            query = query.filter(RequestMetadata.status.in_(status))

        if action:
            query = query.filter(RequestMetadata.action.in_(action))

        if record:
            try:
                uuid = PersistentIdentifier.get("recid", record).object_uuid
                query = query.filter_by(record_id=uuid)
            except Exception:
                query = query.filter(False)
        if summary:
            result = query.group_by(
                RequestMetadata.status, RequestMetadata.action
            ).all()

        if sort:
            column = getattr(Request, sort, None)
            if column:
                if direction == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())

        if page:
            result = query.order_by(RequestMetadata.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )

        return result
