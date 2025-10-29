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

"""Cold Storage FTS plugin."""

import logging
import os

import fts3.rest.client.easy as fts3

logger = logging.getLogger(__name__)


class TransferManager:
    """Plugin to deal with FTS."""

    def __init__(self):
        """Create a TransferManager of type FTS."""
        self.endpoint = os.environ["INVENIO_FTS_ENDPOINT"]
        self._context = None

    def _submit(self, job):
        """Submit a transfer."""
        try:
            if not self._context:
                self._context = fts3.Context(self.endpoint, verify=True)
            job_id = fts3.submit(self._context, job)
        except Exception as my_exc:
            logger.error(f"Error submitting to fts {my_exc}")
            return None
        return job_id

    def _basic_job(self, source, dest):
        """Definition of a job in FTS."""
        # Using https protocol instead of root for all the fts transfers
        return {
            "files": [
                {
                    "sources": [source.replace("root://", "https://")],
                    "destinations": [dest.replace("root://", "https://")],
                }
            ]
        }

    def stage(self, source, dest):
        """Copy from cold to hot."""
        job = self._basic_job(source, dest)

        job["params"] = {"bring_online": 604800, "copy_pin_lifetime": 64000}
        return self._submit(job)

    def archive(self, source, dest):
        """Copy from hot to cold."""
        job = self._basic_job(source, dest)
        job["params"] = {
            "archive_timeout": 86400,
            "copy_pin_lifetime": -1,
        }
        # internal retry logic in case of fail and overwrite to true if it has failed
        a = self._submit(job)
        return a

    def transfer_status(self, transfer_id):
        """Check the status of a transfer."""
        try:
            if not self._context:
                self._context = fts3.Context(self.endpoint, verify=True)
            fts_status = fts3.get_job_status(self._context, transfer_id)
        except Exception as e:
            logger.error(f"Error connecting to fts: {e}")
            return None, None
        if not fts_status:
            logger.error("Error retrieving the status from fts")
            return None, None
        if "job_state" not in fts_status:
            logger.error("The response does not have 'job_state'")
            return None, None
        if fts_status["job_state"] == "FINISHED":
            return "DONE", None
        return fts_status["job_state"], fts_status["reason"]

    def get_endpoint_info(self):
        """Get information from FTS."""
        if not self._context:
            self._context = fts3.Context(self.endpoint, verify=True)
        return self._context.get_endpoint_info()

    def whoami(self):
        """Get the user from FTS."""
        if not self._context:
            self._context = fts3.Context(self.endpoint, verify=True)
        return fts3.whoami(self._context)
