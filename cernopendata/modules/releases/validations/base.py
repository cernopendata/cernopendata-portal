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
"""Top Class to validate releases."""


class Validation:
    """Base validation class."""

    registry = []
    abstract = False

    name = None
    error_message = None
    experiment = None
    optional = False
    applies_to = {"records"}

    def __init_subclass__(cls, **kwargs):
        """Keep a registry of all the validations."""
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "Validation" and not cls.abstract:
            Validation.registry.append(cls)

    def validate(self, release):
        """Validate a release. The method should be implemented in the child classes."""
        raise NotImplementedError

    def fix(self, release):
        """Optional fix method."""
        raise NotImplementedError

    @property
    def fixable(self):
        """Check if a validation has a fix method."""
        return self.fix.__func__ is not Validation.fix
