from cernopendata.modules.releases.validations.metadata import ValidMetadata


class DummyRelease:
    def __init__(self, records=None, documents=None):
        self.records = records or []
        self.documents = documents or []


def test_validate_passes_with_correct_fields():
    validator = ValidMetadata()
    record = {
        "license": {"attribution": "CC0-1.0"},
        "publisher": "CERN Open Data Portal",
    }
    release = DummyRelease(records=[record])
    errors = validator.validate(release)
    assert errors == []


def test_validate_reports_wrong_license_attribution():
    validator = ValidMetadata()
    record = {
        "license": {"attribution": "CC-BY-4.0"},
        "publisher": "CERN Open Data Portal",
    }
    release = DummyRelease(records=[record])
    errors = validator.validate(release)
    assert any("license.attribution" in e for e in errors)
    assert any("CC0-1.0" in e for e in errors)


def test_validate_reports_missing_publisher():
    validator = ValidMetadata()
    record = {"license": {"attribution": "CC0-1.0"}}
    release = DummyRelease(records=[record])
    errors = validator.validate(release)
    assert any("publisher" in e for e in errors)


def test_validate_reports_wrong_publisher():
    validator = ValidMetadata()
    record = {
        "license": {"attribution": "CC0-1.0"},
        "publisher": "Some Other Publisher",
    }
    release = DummyRelease(records=[record])
    errors = validator.validate(release)
    assert any("publisher" in e for e in errors)
    assert any("CERN Open Data Portal" in e for e in errors)


def test_validate_no_records_returns_no_errors():
    validator = ValidMetadata()
    release = DummyRelease(records=[])
    errors = validator.validate(release)
    assert errors == []


def test_validate_ignores_documents():
    validator = ValidMetadata()
    doc_missing_fields = {"title": "some doc"}
    release = DummyRelease(records=[], documents=[doc_missing_fields])
    errors = validator.validate(release)
    assert errors == []


def test_validate_reports_errors_for_each_record():
    validator = ValidMetadata()
    record_a = {"publisher": "Wrong Publisher"}
    record_b = {"publisher": "Also Wrong Publisher"}
    release = DummyRelease(records=[record_a, record_b])
    errors = validator.validate(release)
    assert len(errors) == 4  # license.attribution + publisher for each of the 2 records


def test_fix_sets_expected_fields_on_record():
    validator = ValidMetadata()
    record = {}
    release = DummyRelease(records=[record])
    errors = validator.fix(release)
    assert errors == []
    assert record["license"]["attribution"] == "CC0-1.0"
    assert record["publisher"] == "CERN Open Data Portal"


def test_fix_overwrites_wrong_values():
    validator = ValidMetadata()
    record = {"license": {"attribution": "CC-BY-4.0"}, "publisher": "Wrong"}
    release = DummyRelease(records=[record])
    errors = validator.fix(release)
    assert errors == []
    assert record["license"]["attribution"] == "CC0-1.0"
    assert record["publisher"] == "CERN Open Data Portal"


def test_fix_no_records_returns_no_errors():
    validator = ValidMetadata()
    release = DummyRelease(records=[])
    errors = validator.fix(release)
    assert errors == []
