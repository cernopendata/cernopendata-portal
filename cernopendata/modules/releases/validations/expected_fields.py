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

    abstract = True

    def get_nested(self, data, path):
        """Get a value (which might be nested."""
        keys = path.split(".")
        for key in keys:
            if data is None:
                return None
            data = data.get(key)
        return data

    def resolve_expected_value(self, expected, release, item):
        """Get the expected value of a field for an item."""
        # If callable → compute value dynamically
        if callable(expected):
            return expected(release, item)
        return expected

    def _check_field(self, label, i, item, field, expected_value):
        """Return an error message if the field doesn't match the expected value, else None."""
        if not expected_value:
            return f"{label} {i + 1}, field {field}: can't figure out what the value is supposed to be"
        actual_value = self.get_nested(item, field)
        if actual_value != expected_value:
            return f"{label} {i + 1}, field {field}: expected: '{expected_value}' and got '{actual_value}'"
        return None

    def _fix_field(self, label, i, item, field, expected_value):
        """Set the field to its expected value. Returns an error if the value can't be determined."""
        if not expected_value:
            return f"{label} {i + 1}, field {field}: can't figure out what the value is supposed to be"
        self.set_nested(item, field, expected_value)
        return None

    def validate(self, release):
        """Validation that all the fields have the expected values."""
        errors = []
        for kind, label in (("records", "Record"), ("documents", "Document")):
            if kind not in self.applies_to:
                continue
            items = getattr(release, kind) or []
            for field, expected in self.expected_fields.items():
                for i, item in enumerate(items):
                    expected_value = self.resolve_expected_value(
                        expected, release, item
                    )
                    error = self._check_field(label, i, item, field, expected_value)
                    if error:
                        errors.append(error)
        return errors

    def fix(self, release):
        """Fix all the fields, setting the expected value for each of them."""
        errors = []
        for kind, label in (("records", "Record"), ("documents", "Document")):
            if kind not in self.applies_to:
                continue
            items = getattr(release, kind) or []
            for field, expected in self.expected_fields.items():
                for i, item in enumerate(items):
                    expected_value = self.resolve_expected_value(
                        expected, release, item
                    )
                    error = self._fix_field(label, i, item, field, expected_value)
                    if error:
                        errors.append(error)
        return errors

    def set_nested(self, data, path, value):
        """Set a value for a field in a record."""
        keys = path.split(".")
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value
