"""Validation process."""

from .schema import SchemaValidation


class ValidRecordSchema(SchemaValidation):
    """Check that the records validate the JSON schema."""

    abstract = False
    name = "Valid record schema"
    error_message = "The records do not comply with the JSON schema."
    schema_file = "records/record-v1.0.0.json"
    items_attr = "records"
    label = "Record"
