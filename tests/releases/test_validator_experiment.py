import pytest

from cernopendata.modules.releases.validations.experiment import ValidExperiment


class DummyMetadata:
    def __init__(self, experiment):
        self.experiment = experiment


class DummyRelease:
    def __init__(self, records, experiment="cms"):
        self.records = records
        self._metadata = DummyMetadata(experiment)


def test_missing_experiment():
    release = DummyRelease([{}])
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == ["Entry 0: 'experiment' field is missing"]


def test_experiment_not_list():
    release = DummyRelease([{"experiment": "CMS"}])
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == ["Entry 0: 'experiment' must be a list"]


def test_wrong_experiment_value():
    release = DummyRelease([{"experiment": ["ATLAS"]}], experiment="cms")
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == ["Entry 0: 'experiment' must contain only 'cms'"]


def test_two_experiments_value():
    release = DummyRelease([{"experiment": ["ATLAS", "CMS"]}], experiment="cms")
    validator = ValidExperiment()

    errors = validator.validate(release)

    assert errors == ["Entry 0: 'experiment' must contain only 'cms'"]


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
