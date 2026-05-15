from cernopendata.modules.releases.validations.expected_fields import (
    ExpectedFieldsValidation,
)


class DummyRelease:
    def __init__(self, records=None, documents=None):
        self.records = records or []
        self.documents = documents or []


class _RecordValidator(ExpectedFieldsValidation):
    abstract = False
    applies_to = {"records"}
    name = "record-only"
    error_message = "record-only"
    expected_fields = {"experiment": lambda release, record=None: None}


class _DocValidator(ExpectedFieldsValidation):
    abstract = False
    applies_to = {"documents"}
    name = "doc-only"
    error_message = "doc-only"
    expected_fields = {"experiment": lambda release, doc=None: None}


class _StaticValueValidator(ExpectedFieldsValidation):
    abstract = False
    applies_to = {"records"}
    name = "static-value"
    error_message = "static-value"
    expected_fields = {"experiment": ["CMS"]}


def test_resolve_expected_value_returns_static_value():
    validator = _StaticValueValidator()
    release = DummyRelease(records=[{"experiment": ["CMS"]}])
    errors = validator.validate(release)
    assert errors == []


def test_resolve_expected_value_static_mismatch():
    validator = _StaticValueValidator()
    release = DummyRelease(records=[{"experiment": ["ATLAS"]}])
    errors = validator.validate(release)
    assert errors == [
        "Record 1, field experiment: expected: '['CMS']' and got '['ATLAS']'"
    ]


def test_check_field_returns_error_when_expected_value_falsy():
    validator = _RecordValidator()
    release = DummyRelease(records=[{"experiment": ["CMS"]}])
    errors = validator.validate(release)
    assert errors == [
        "Record 1, field experiment: can't figure out what the value is supposed to be"
    ]


def test_fix_records_collects_unresolvable_errors():
    validator = _RecordValidator()
    release = DummyRelease(records=[{"experiment": ["CMS"]}])
    errors = validator.fix(release)
    assert errors == [
        "Record 1, field experiment: can't figure out what the value is supposed to be"
    ]


def test_fix_documents_collects_unresolvable_errors():
    validator = _DocValidator()
    release = DummyRelease(documents=[{"experiment": ["CMS"]}])
    errors = validator.fix(release)
    assert errors == [
        "Document 1, field experiment: can't figure out what the value is supposed to be"
    ]
