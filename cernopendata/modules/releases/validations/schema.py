"""Validation process."""

import json

from flask import current_app
from jsonschema import Draft4Validator

from .base import Validation


class SchemaValidation(Validation):
    """Abstract base class for validating release items against a JSON schema."""

    abstract = True

    schema_file = None
    items_attr = None
    label = None
    excluded_keys = set()

    def validate(self, release):
        """Validate all items against the configured JSON schema."""
        schema_path = (
            current_app.extensions["invenio-jsonschemas"].get_schema_dir(
                self.schema_file
            )
            + f"/{self.schema_file}"
        )
        try:
            with open(schema_path) as f:
                schema = json.load(f)
        except (OSError, ValueError) as e:
            return [f"Could not load validation schema '{self.schema_file}': {e}"]

        items = getattr(release, self.items_attr) or []
        if not items:
            return []
        if not isinstance(items, list):
            return [f"The field '{self.items_attr}' is not a list"]

        errors = []
        validator = Draft4Validator(schema)
        try:
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"{self.label} {i + 1} is not an object")
                    continue
                if self.excluded_keys:
                    item = {
                        k: v for k, v in item.items() if k not in self.excluded_keys
                    }
                for error in validator.iter_errors(item):
                    path = ".".join(str(p) for p in error.path)
                    errors.append(f"{self.label} {i + 1} -> {path}: {error.message}")
        except Exception as e:
            return [f"Could not validate the schema: {e}"]

        return errors
