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


class ExpectedFieldsValidation(Validation):
    """Abstract class that offers a dictionary of fields and expected values."""

    expected_fields = {}
    expected_record_fields = {}

    abstract = True

    def get_nested(self, data, path):
        """Get a value (which might be nested."""
        keys = path.split(".")
        for key in keys:
            if data is None:
                return None
            data = data.get(key)
        return data

    def resolve_expected_value(self, expected, release, record):
        """Get the expected value of a field for a record."""
        # If callable → compute value dynamically
        if callable(expected):
            return expected(release, record)
        return expected

    def validate(self, release):
        """Valiation that all the fields have the expected values."""
        errors = []

        for field, expected in self.expected_fields.items():
            for i, record in enumerate(release.records):
                expected_value = self.resolve_expected_value(expected, release, record)
                if not expected_value:
                    errors.append(
                        f"Record {i}, field {field}: can't figure out what the value is supposed to be"
                    )
                    continue
                actual_value = self.get_nested(record, field)

                if actual_value != expected_value:
                    errors.append(
                        f"Record {i}, field {field}: expected: '{expected_value}' and got '{actual_value}'"
                    )

        return errors

    def fix(self, release):
        """Fix all the fields, setting the expected value for each of them."""
        for field, expected in self.expected_fields.items():
            for record in release.records:
                expected_value = self.resolve_expected_value(expected, release, record)
                if not expected_value:
                    errors.append(
                        f"Record {i}, field {field}: can't figure out what the value is supposed to be"
                    )
                    continue
                self.set_nested(record, field, expected_value)

        return []

    def set_nested(self, data, path, value):
        """Set a value for a field in a record."""
        keys = path.split(".")
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value
