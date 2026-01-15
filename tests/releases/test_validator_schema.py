import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from cernopendata.modules.releases.api import Release
from cernopendata.modules.releases.validations.schema import ValidRecordSchema


@pytest.fixture
def dummy_release():
    """Create a dummy release object with records."""
    release = MagicMock(spec=Release)
    release.records = [
        {"title": "Record 1", "recid": "1"},  # valid
        "not_a_dict",  # invalid type
        {"title": "Record 2"},  # missing recid
    ]
    return release


VALID_SCHEMA = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "recid": {"type": "string"}},
    "required": ["title", "recid"],
}


def test_validate_records_success(app):
    """Test that a valid record passes schema validation."""
    # Setup
    with app.app_context():
        # Patch open to return a schema
        with patch("builtins.open", mock_open(read_data=json.dumps(VALID_SCHEMA))):
            release = MagicMock()
            release.records = [{"title": "Record 1", "recid": "1"}]

            validator = ValidRecordSchema()
            errors = validator.validate(release)
            assert errors == []


def test_validate_records_type_and_missing_fields(app):
    """Test invalid record types and missing required fields."""
    with app.app_context():
        # Patch open to return a schema
        with patch("builtins.open", mock_open(read_data=json.dumps(VALID_SCHEMA))):
            release = MagicMock()
            release.records = [
                "not_a_dict",
                {"title": "Only title"},
            ]

            validator = ValidRecordSchema()
            errors = validator.validate(release)
            assert len(errors) == 2
            assert "not_a_dict" not in errors[0]  # error message includes index
            assert "Record 0 is not an object" in errors[0]
            assert "recid" in errors[1]  # missing recid triggers schema error


def test_validate_records_not_list(app):
    """Test when release.records is not a list."""
    with app.app_context():
        release = MagicMock()
        release.records = "not_a_list"
        with app.app_context():
            validator = ValidRecordSchema()
        errors = validator.validate(release)
        assert errors == ["The field 'records' is not a list"]
