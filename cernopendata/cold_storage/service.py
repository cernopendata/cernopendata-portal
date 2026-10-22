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

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy import case, func

from cernopendata.api import RecordFilesWithIndex

from .api import ColdStorageActions, RecordAvailability, Request, Transfer
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
        finished_transfers = []
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
                finished_transfers.append(transfer)
            if transfer.status == "FAILED" or not transfer.status:
                logger.error(f"The transfer {id} failed :(")
                transfer.reason = error
                transfer.finished = datetime.now()
            else:
                logger.debug(f"Transfer {id} is in status {transfer.status}")
            db.session.add(transfer)
            db.session.commit()
        failed_records = catalog.reindex_entries()
        for transfer in finished_transfers:
            if transfer.record_uuid in failed_records:
                transfer.reason = (
                    f"Record not updated: {failed_records[transfer.record_uuid]}"
                )
                db.session.add(transfer)
        db.session.commit()
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
        for action in ColdStorageActions:
            active_transfers_count = TransferMetadata.query.filter(
                TransferMetadata.finished.is_(None),
                TransferMetadata.action == action.value,
            ).count()
            threshold = Transfer.get_active_transfers_threshold(action)

            if not threshold:
                logger.info(
                    f"For the action {action.value} there is no threshold. Ignoring"
                )
                continue

            logger.info(
                f"Checking if we can {action.value} more records: active {active_transfers_count}/{threshold}"
            )

            submitted_count = 0
            max_transfers = threshold - active_transfers_count
            if max_transfers > 0:
                requests = RequestMetadata.query.filter_by(
                    status="submitted", action=action.value
                ).all()

                for request in requests:
                    try:
                        submitted_transfers = manager.doOperation(
                            action,
                            request.record_id,
                            limit=None,
                            register=True,
                            force=False,
                            dry=False,
                            max_transfers=max_transfers - submitted_count,
                            file=request.file,
                            request_id=request.id,
                        )
                        if submitted_transfers:
                            submitted_count += len(submitted_transfers)
                            request.num_transfers += len(submitted_transfers)
                        request.started_at = datetime.utcnow()
                        logger.info(
                            f"Request {request.id}: {submitted_count}/{max_transfers} transfers submitted"
                        )
                        if max_transfers == submitted_count:
                            logger.info(
                                f"Request {request.id}: reached the threshold of {threshold}"
                                " transfers, continuing in the next run"
                            )
                        elif (
                            submitted_transfers
                            or RequestService._request_files_staged(
                                RecordFilesWithIndex.get_record(request.record_id),
                                request,
                            )
                        ):
                            request.status = "started"
                        else:
                            logger.error(
                                f"Request {request.id}: no transfers could be issued,"
                                " retrying in the next run"
                            )
                        db.session.add(request)
                        db.session.commit()
                    except Exception as e:
                        logger.exception(
                            f"Error submitting request {request.id}, skipping it: {e}"
                        )
                        db.session.rollback()
                        continue
                    if max_transfers - submitted_count <= 0:
                        logger.info("We have submitted enough. Stopping")
                        break
            if submitted_count:
                logger.info(f"{submitted_count} transfers have been submitted!")

    @staticmethod
    def _request_files_staged(record, request):
        """Check if all the files of a request have a hot copy."""
        files = Catalog().get_files_from_record(record, file=request.file)
        if not files:
            return False
        return all("hot_deleted" not in file.get("tags", {}) for file in files)

    @staticmethod
    def check_running():
        """Check the records that are being archived."""
        manager = ColdStorageManager()
        for action in ColdStorageActions:
            requests = RequestMetadata.query.filter_by(
                status="started", action=action.value
            ).all()
            logger.debug(f"Checking the {len(requests)} {action.value} requests")
            active_transfers_count = TransferMetadata.query.filter(
                TransferMetadata.finished.is_(None),
                TransferMetadata.action == action.value,
            ).count()
            max_transfers = (
                Transfer.get_active_transfers_threshold(action) or 0
            ) - active_transfers_count
            completed = 0
            for request in requests:
                try:
                    record = RecordFilesWithIndex.get_record(request.record_id)
                    request.num_failed_transfers = Transfer.get_failed_transfers_count(
                        request
                    )
                    request.size = Transfer.get_completed_transfers_size(request)
                    db.session.add(request)
                    if action == ColdStorageActions.STAGE:
                        if record["availability"] != RecordAvailability.ONLINE.value:
                            logger.info(
                                f"Request {request.id}: rechecking availability"
                            )
                            Catalog().save_record_availability(record)
                        if not RequestService._request_files_staged(record, request):
                            if Transfer.get_active_transfers_count(request):
                                logger.info(
                                    f"Request {request.id}: transfers still in progress"
                                )
                                continue
                            submitted_transfers = []
                            if max_transfers > 0:
                                submitted_transfers = manager.doOperation(
                                    action,
                                    request.record_id,
                                    limit=None,
                                    register=True,
                                    force=False,
                                    dry=False,
                                    max_transfers=max_transfers,
                                    file=request.file,
                                    request_id=request.id,
                                )
                            if submitted_transfers:
                                max_transfers -= len(submitted_transfers)
                                request.num_transfers += len(submitted_transfers)
                                db.session.add(request)
                                db.session.commit()
                                logger.info(
                                    f"Request {request.id}: files still cold,"
                                    f" {len(submitted_transfers)} transfers resubmitted"
                                )
                            else:
                                logger.warning(
                                    f"Request {request.id}: files still cold and no transfers"
                                    " could be resubmitted, retrying in the next run"
                                )
                            continue
                    elif action == ColdStorageActions.ARCHIVE:
                        files = (
                            f for index in record.file_indices for f in index["files"]
                        )
                        missing_file = next(
                            (
                                f
                                for f in files
                                if "tags" not in f or "uri_cold" not in f["tags"]
                            ),
                            None,
                        )
                        if missing_file:
                            logger.debug(
                                f"Request {request.id}: file {missing_file['key']} not on tape yet"
                            )
                            continue
                    Request.mark_as_completed(request)
                    completed += 1
                except Exception as e:
                    logger.exception(
                        f"Error checking request {request.id}, skipping it: {e}"
                    )
                    db.session.rollback()
            db.session.commit()
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
                func.sum(RequestMetadata.num_transfers).label("files"),
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
            # Sort by successful transfers (total - failed, clamped to 0) or by column
            if sort == "num_transfers":
                total = func.coalesce(RequestMetadata.num_transfers, 0)
                failed = func.coalesce(RequestMetadata.num_failed_transfers, 0)
                successful = total - failed
                sort_expr = case((successful < 0, 0), else_=successful)
            else:
                sort_expr = getattr(RequestMetadata, sort, None)

            if sort_expr is not None:
                order = sort_expr.desc() if direction == "desc" else sort_expr.asc()
                query = query.order_by(order)
        else:
            query = query.order_by(RequestMetadata.created_at.desc())

        if page:
            result = query.paginate(page=page, per_page=per_page, error_out=False)

        return result
