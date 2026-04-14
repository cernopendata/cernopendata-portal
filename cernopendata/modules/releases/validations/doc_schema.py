"""Validation process."""

from .schema import SchemaValidation


class ValidDocSchema(SchemaValidation):
    """Check that the documents validate the JSON schema."""

    abstract = False
    name = "Valid document schema"
    error_message = "The documents do not comply with the JSON schema."
    applies_to = {"documents"}
    schema_file = "records/docs-v1.0.0.json"
    items_attr = "documents"
    label = "Document"
    excluded_keys = {"_source_filename"}
