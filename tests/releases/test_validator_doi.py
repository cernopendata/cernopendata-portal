from unittest.mock import patch

import pytest

from cernopendata.modules.releases.validations.doi import ValidDoi

TEST_PREFIX = "10.5072"
WRONG_PREFIX = "10.9999"
SUFFIX = "OPENDATA.CMS.AB12.CD34"


class DummyRelease:
    def __init__(self, records, experiment="CMS"):
        self.records = records
        self.experiment = experiment


def _config(instance_name):
    return {
        "PIDSTORE_DATACITE_DOI_PREFIX": TEST_PREFIX,
        "INSTANCE_NAME": instance_name,
    }


@pytest.fixture
def patched_prefix():
    with patch("cernopendata.modules.releases.validations.doi.current_app") as mock_app:
        mock_app.config = _config("opendata")
        yield


@pytest.fixture
def patched_prefix_nonprod():
    with patch("cernopendata.modules.releases.validations.doi.current_app") as mock_app:
        mock_app.config = _config("opendata-dev")
        yield


@pytest.mark.parametrize(
    "records, registered, expected",
    [
        ([{"recid": "CMS-1"}, {"recid": "CMS-2"}], [], None),
        ([{"recid": "CMS-1", "doi": "not-a-doi"}], [], "Malformed DOI"),
        ([{"recid": "CMS-1", "doi": f"{WRONG_PREFIX}/{SUFFIX}"}], [], "does not match"),
        (
            [
                {"recid": "CMS-1", "doi": f"{TEST_PREFIX}/{SUFFIX}"},
                {"recid": "CMS-2", "doi": f"{TEST_PREFIX}/{SUFFIX}"},
            ],
            [],
            "Duplicate DOI suffix",
        ),
        (
            [{"recid": "CMS-1", "doi": f"{TEST_PREFIX}/{SUFFIX}"}],
            [SUFFIX],
            "already registered",
        ),
        ([{"recid": "CMS-1", "doi": f"{TEST_PREFIX}/{SUFFIX}"}], [], None),
    ],
)
def test_validate(patched_prefix, records, registered, expected):
    validator = ValidDoi()
    release = DummyRelease(records)
    with patch.object(validator, "_registered_suffixes", return_value=registered), patch(
        "cernopendata.modules.releases.validations.doi.validate_record"
    ):
        errors = validator.validate(release)
    if expected is None:
        assert errors == []
    else:
        assert len(errors) == 1
        assert expected in errors[0]


def test_fix_corrects_prefix_and_mints_duplicate(patched_prefix):
    minted = f"{TEST_PREFIX}/OPENDATA.CMS.ZZZZ.9999"
    validator = ValidDoi()
    release = DummyRelease(
        [
            {"recid": "CMS-0"},
            {"recid": "CMS-1", "doi": f"{WRONG_PREFIX}/{SUFFIX}"},
            {"recid": "CMS-2", "doi": f"{TEST_PREFIX}/{SUFFIX}"},
        ]
    )
    with patch.object(validator, "_registered_suffixes", return_value=[]), patch(
        "cernopendata.modules.releases.validations.doi.generate_doi",
        return_value=minted,
    ), patch("cernopendata.modules.releases.validations.doi.validate_record"):
        errors = validator.fix(release)
    assert "doi" not in release.records[0]
    assert release.records[1]["doi"] == f"{TEST_PREFIX}/{SUFFIX}"
    assert release.records[2]["doi"] == minted
    assert errors == []


def test_fix_mints_new_doi_for_malformed(patched_prefix):
    minted = f"{TEST_PREFIX}/OPENDATA.CMS.ZZZZ.9999"
    validator = ValidDoi()
    release = DummyRelease([{"recid": "CMS-1", "doi": "not-a-doi"}])
    with patch.object(validator, "_registered_suffixes", return_value=[]), patch(
        "cernopendata.modules.releases.validations.doi.generate_doi",
        return_value=minted,
    ), patch("cernopendata.modules.releases.validations.doi.validate_record"):
        errors = validator.fix(release)
    assert release.records[0]["doi"] == minted
    assert errors == []


def test_validate_allows_wrong_prefix_in_non_production(patched_prefix_nonprod):
    validator = ValidDoi()
    release = DummyRelease([{"recid": "CMS-1", "doi": f"{WRONG_PREFIX}/{SUFFIX}"}])
    with patch.object(validator, "_registered_suffixes", return_value=[]), patch(
        "cernopendata.modules.releases.validations.doi.validate_record"
    ):
        assert validator.validate(release) == []


def test_fix_keeps_wrong_prefix_in_non_production(patched_prefix_nonprod):
    validator = ValidDoi()
    release = DummyRelease([{"recid": "CMS-1", "doi": f"{WRONG_PREFIX}/{SUFFIX}"}])
    with patch.object(validator, "_registered_suffixes", return_value=[]), patch(
        "cernopendata.modules.releases.validations.doi.validate_record"
    ):
        assert validator.fix(release) == []
    assert release.records[0]["doi"] == f"{WRONG_PREFIX}/{SUFFIX}"


def test_registered_suffixes_empty():
    assert ValidDoi._registered_suffixes(TEST_PREFIX, []) == []


def test_registered_suffixes_matches_existing():
    class FakePid:
        pid_value = f"{TEST_PREFIX}/{SUFFIX}"

    with patch(
        "cernopendata.modules.releases.validations.doi.PersistentIdentifier"
    ) as mock_pid:
        mock_pid.query.filter.return_value.all.return_value = [FakePid()]
        result = ValidDoi._registered_suffixes(TEST_PREFIX, [SUFFIX])
    assert result == [SUFFIX]


def test_validate_datacite_metadata_failure(patched_prefix):
    validator = ValidDoi()
    release = DummyRelease([{"recid": "CMS-1", "doi": f"{TEST_PREFIX}/{SUFFIX}"}])
    with patch.object(validator, "_registered_suffixes", return_value=[]), patch(
        "cernopendata.modules.releases.validations.doi.validate_record",
        side_effect=ValueError("No creators"),
    ):
        errors = validator.validate(release)
    assert len(errors) == 1
    assert "Record CMS-1: Invalid DataCite metadata: No creators" in errors[0]
