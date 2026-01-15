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
"""Validation process."""
from .base import Validation


class ValidExperiment(Validation):
    """Check that the experiment is properly defined."""

    name = "Valid experiment"
    error_message = "The records should be of the correct experiment."

    def validate(self, release):
        """Check that the experiment is properly defined."""
        errors = []
        for i, entry in enumerate(release.records):
            exp_list = entry.get("experiment")
            if exp_list is None:
                error = "field is missing"
            elif not isinstance(exp_list, list):
                error = "must be a list"
            elif any(exp != release._metadata.experiment.upper() for exp in exp_list):
                error = f"must contain only '{release._metadata.experiment}'"
            else:
                continue
            errors.append(f"Entry {i}: 'experiment' {error}")
        return errors

    def fix(self, release):
        """Put the experiment in all the records."""
        for record in release.records:
            record["experiment"] = [release._metadata.experiment.upper()]
        return []
