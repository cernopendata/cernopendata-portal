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

# This requires to install swig: yum install swig. Let's wait a bit
import fts3.rest.client.easy as fts3
import gfal2


class TransferManager:
    """Plugin to deal with FTS."""

    def __init__(self):
        """Create a TransferManager of type FTS."""
        endpoint = os.environ["INVENIO_FTS_ENDPOINT"]
        self._context = fts3.Context(endpoint, verify=True)
        self._logger = logging.getLogger(__name__)
        if debug:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

    def _submit(self, job):
        """Submit a transfer."""
        # print("Submiting to fts", job)
        try:
            job_id = fts3.submit(self._context, job)
        except Exception as my_exc:
            self._logger.error(f"Error submitting to fts {my_exc}")
            return None
        return job_id

    def _basic_job(self, source, dest):
        """Definition of a job in FTS."""
        return {"files": [{"sources": [source], "destinations": [dest]}]}

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
        # print("FTS RETURNS",a)
        return a

    def transfer_status(self, transfer_id):
        """Check the status of a transfer."""
        try:
            fts_status = fts3.get_job_status(self._context, transfer_id)
        except Exception as e:
            self._logger.error(f"Error connecting to fts: {e}")
            return None, None
        if not fts_status:
            self._logger.error("Error retrieving the status from fts")
            return None, None
        if "job_state" not in fts_status:
            self._logger.error("The response does not have 'job_state'")
            return None, None
        # print("The status in fts is", fts_status['job_state'])
        if fts_status["job_state"] == "FINISHED":
            return "DONE", None
        return fts_status["job_state"], fts_status["reason"]

    def get_endpoint_info(self):
        """Get information from FTS."""
        return self._context.get_endpoint_info()

    def whoami(self):
        """Get the user from FTS."""
        return fts3.whoami(self._context)

    def exists_file(self, filename):
        """Check if a file exists."""
        ctx = gfal2.creat_context()

        self._logger.debug(f"Checking with gfal if {filename} exists")
        try:
            info = ctx.stat(filename)
            checksum = ctx.checksum(filename, "ADLER32")

            return {"size": info.st_size, "checksum": checksum}
        except Exception as e:
            pass
        return False
