"""Validation process."""

import json

from flask import current_app
from jsonschema import Draft4Validator

from .base import Validation


class ValidRecordSchema(Validation):
    """Check that the record validates the json schema."""

    name = "Valid record schema"
    error_message = "The records do not comply with the json schema."

    def validate(self, release):
        """Validate all records against record-v1.0.0.json."""
        schema_path = (
            current_app.extensions["invenio-jsonschemas"].get_schema_dir(
                "records/record-v1.0.0.json"
            )
            + "/records/record-v1.0.0.json"
        )
        with open(schema_path) as f:
            schema = json.load(f)
        errors = []
        validator = Draft4Validator(schema)
        if not isinstance(release.records, list):
            return ["The field 'records' is not a list"]

        try:
            for i, record in enumerate(release.records):
                if not isinstance(record, dict):
                    errors.append(f"Record {i} is not an object")
                    continue
                for error in validator.iter_errors(record):
                    path = ".".join(str(p) for p in error.path)

                    errors.append(f"Record {i} -> {path}: {error.message}")
        except Exception as e:
            return [f"Could not validate the schema {e}"]

        return errors
