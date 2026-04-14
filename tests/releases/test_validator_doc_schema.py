import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from cernopendata.modules.releases.validations.doc_schema import ValidDocSchema

VALID_SCHEMA = {
    "type": "object",
    "properties": {
        "slug": {"type": "string"},
        "title": {"type": "string"},
    },
    "required": ["slug", "title"],
}


def test_validate_passes_for_valid_document(app):
    with app.app_context():
        with patch("builtins.open", mock_open(read_data=json.dumps(VALID_SCHEMA))):
            release = MagicMock()
            release.documents = [{"slug": "alice-data-2015", "title": "Alice data"}]
            validator = ValidDocSchema()
            errors = validator.validate(release)
    assert errors == []


def test_validate_reports_missing_required_field(app):
    with app.app_context():
        with patch("builtins.open", mock_open(read_data=json.dumps(VALID_SCHEMA))):
            release = MagicMock()
            release.documents = [{"slug": "alice-data-2015"}]
            validator = ValidDocSchema()
            errors = validator.validate(release)
    assert len(errors) == 1
    assert "title" in errors[0]


def test_validate_reports_non_dict_document(app):
    with app.app_context():
        with patch("builtins.open", mock_open(read_data=json.dumps(VALID_SCHEMA))):
            release = MagicMock()
            release.documents = ["not_a_dict"]
            validator = ValidDocSchema()
            errors = validator.validate(release)
    assert any("not an object" in e for e in errors)


def test_validate_strips_source_filename_before_validating(app):
    with app.app_context():
        with patch("builtins.open", mock_open(read_data=json.dumps(VALID_SCHEMA))):
            release = MagicMock()
            release.documents = [
                {
                    "slug": "alice-data-2015",
                    "title": "Alice data",
                    "_source_filename": "alice-data-2015.json",
                }
            ]
            validator = ValidDocSchema()
            errors = validator.validate(release)
    assert errors == []


def test_validate_returns_empty_when_no_documents(app):
    with app.app_context():
        release = MagicMock()
        release.documents = []
        validator = ValidDocSchema()
        errors = validator.validate(release)
    assert errors == []
