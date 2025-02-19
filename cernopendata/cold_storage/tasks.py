# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2025 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tasks for the Cold Storage."""

from datetime import timedelta

from celery import shared_task
from flask.cli import with_appcontext

from .service import RequestService, TransferService

CheckTransfersTask = {
    "task": "cernopendata.cold_storage.tasks.check_transfers",
    "schedule": timedelta(minutes=30),
}


@shared_task
@with_appcontext
def check_transfers():
    """Check the ongoing transfers."""
    RequestService.process_requests()
    TransferService.process_transfers()
