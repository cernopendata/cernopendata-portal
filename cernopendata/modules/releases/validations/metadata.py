"""Validation process."""

from .expected_fields import ExpectedFieldsValidation


class ValidMetadata(ExpectedFieldsValidation):
    """Check some common fields of the records."""

    abstract = False

    name = "Valid standard fields"
    error_message = "Some records are missing some of the standard fields"
    expected_fields = {
        "license.attribution": "CC0-1.0",
        "publisher": "CERN Open Data Portal",
    }
