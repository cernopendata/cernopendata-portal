import pytest

from cernopendata.modules.releases.validations.experiment import ValidExperiment


class DummyRelease:
    def __init__(self, records, experiment="cms", documents=None):
        self.records = records
        self.documents = documents or []
        self.experiment = experiment


def test_missing_experiment():
    release = DummyRelease([{}])
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == ["Record 0, field experiment: expected: '['CMS']' and got 'None'"]


def test_experiment_not_list():
    release = DummyRelease([{"experiment": "CMS"}])
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == ["Record 0, field experiment: expected: '['CMS']' and got 'CMS'"]


def test_wrong_experiment_value():
    release = DummyRelease([{"experiment": ["ATLAS"]}], experiment="cms")
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == [
        "Record 0, field experiment: expected: '['CMS']' and got '['ATLAS']'"
    ]


def test_two_experiments_value():
    release = DummyRelease([{"experiment": ["ATLAS", "CMS"]}], experiment="cms")
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == [
        "Record 0, field experiment: expected: '['CMS']' and got '['ATLAS', 'CMS']'"
    ]


def test_valid_experiment():
    release = DummyRelease([{"experiment": ["CMS"]}], experiment="cms")
    validator = ValidExperiment()

    errors = validator.validate(release)
    assert errors == []


def test_fix_sets_experiment():
    release = DummyRelease([{}, {"experiment": ["ATLAS"]}], experiment="cms")
    validator = ValidExperiment()

    errors = validator.fix(release)

    assert errors == []
    for record in release.records:
        assert record["experiment"] == ["CMS"]


def test_valid_experiment_doc_passes():
    release = DummyRelease([], experiment="cms", documents=[{"experiment": ["CMS"]}])
    validator = ValidExperiment()
    errors = validator.validate(release)
    assert errors == []


def test_valid_experiment_doc_wrong_experiment():
    release = DummyRelease([], experiment="cms", documents=[{"experiment": ["ALICE"]}])
    validator = ValidExperiment()
    errors = validator.validate(release)
    assert any("Document 0" in e for e in errors)


def test_valid_experiment_doc_missing_field():
    release = DummyRelease([], experiment="cms", documents=[{"title": "no experiment"}])
    validator = ValidExperiment()
    errors = validator.validate(release)
    assert any("Document 0" in e for e in errors)


def test_fix_sets_experiment_on_documents():
    release = DummyRelease(
        [], experiment="cms", documents=[{}, {"experiment": ["ATLAS"]}]
    )
    validator = ValidExperiment()
    errors = validator.fix(release)
    assert errors == []
    for doc in release.documents:
        assert doc["experiment"] == ["CMS"]
