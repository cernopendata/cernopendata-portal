"""Validation process."""

import json

from flask import current_app
from jsonschema import Draft4Validator

from .base import Validation


class ValidDocSchema(Validation):
    """Check that the document validates the json schema."""

    name = "Valid document schema"
    error_message = "The documents do not comply with the json schema."
    applies_to = {"documents"}

    def validate(self, release):
        """Validate all documents against docs-v1.0.0.json."""
        schema_path = (
            current_app.extensions["invenio-jsonschemas"].get_schema_dir(
                "records/docs-v1.0.0.json"
            )
            + "/records/docs-v1.0.0.json"
        )
        with open(schema_path) as f:
            schema = json.load(f)
        documents = release.documents or []
        if not documents:
            return []

        errors = []
        validator = Draft4Validator(schema)
        if not isinstance(documents, list):
            return ["The field 'documents' is not a list"]

        try:
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict):
                    errors.append(f"Document {i} is not an object")
                    continue
                doc_copy = {k: v for k, v in doc.items() if k != "_source_filename"}
                for error in validator.iter_errors(doc_copy):
                    path = ".".join(str(p) for p in error.path)
                    errors.append(f"Document {i} -> {path}: {error.message}")
        except Exception as e:
            return [f"Could not validate the schema {e}"]

        return errors
