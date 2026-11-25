# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2025 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tasks for the Cold Storage."""

import logging
from datetime import timedelta

from celery import shared_task
from flask.cli import with_appcontext
from invenio_db import db

from .cli import setup_cold_logging
from .service import RequestService, TransferService

logger = logging.getLogger(__name__)

CheckTransfersTask = {
    "task": "cernopendata.cold_storage.tasks.check_transfers",
    "schedule": timedelta(minutes=30),
}


@shared_task
@with_appcontext
def check_transfers():
    """Check the ongoing transfers."""
    setup_cold_logging()

    try:
        RequestService.process_requests()
    except Exception as e:
        logger.exception(f"Error processing the requests: {e}")
        db.session.rollback()

    try:
        TransferService.process_transfers()
    except Exception as e:
        logger.exception(f"Error processing the transfers: {e}")
        db.session.rollback()
