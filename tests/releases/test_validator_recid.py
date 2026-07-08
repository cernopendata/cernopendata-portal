from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases.models import ReleaseStatus
from cernopendata.modules.releases.validations.recid import ValidRecid


class DummyRelease:
    def __init__(self, records, experiment="CMS", status="DRAFT", max_recid=0):
        self.records = records
        self.experiment = experiment
        self.status = ReleaseStatus[status].value
        self.max_recid = max_recid


def test_validator_recid_fix():
    validator = ValidRecid()
    release = DummyRelease(
        [
            {"title": "no recid"},
            {"recid": "CMS-42"},
            {"recid": "CMS-7"},
            {"recid": "80000"},
            {"recid": "90000"},
            {"recid": "garbage"},
        ]
    )
    with patch.object(validator, "next_recid_start", return_value=100), patch.object(
        validator, "_duplicate_pids", return_value=["CMS-7", "90000"]
    ), patch.object(validator, "_numeric_collisions", return_value=[]):
        errors = validator.fix(release)

    assert errors == []
    assert [record["recid"] for record in release.records] == [
        "CMS-100",
        "CMS-42",
        "CMS-101",
        "CMS-80000",
        "CMS-102",
        "CMS-103",
    ]
    assert release.max_recid == 103


def test_validator_recid_validate():
    validator = ValidRecid()
    release = DummyRelease([{"recid": "CMS-5"}, {"recid": "80000"}])
    with patch.object(validator, "_duplicate_pids", return_value=[]), patch.object(
        validator, "_numeric_collisions", return_value=[]
    ):
        errors = validator.validate(release)
    assert any("80000" in error and "does not match" in error for error in errors)
    assert not any("CMS-5" in error for error in errors)


@pytest.mark.parametrize(
    "max_release, max_registered, max_numeric, expected",
    [
        (None, 80500, None, 80501),
        (100, 50, None, 101),
        (None, None, 90000, 90001),
        (None, None, None, 1),
    ],
)
def test_validator_recid_next_recid_start(
    max_release, max_registered, max_numeric, expected
):
    validator = ValidRecid()
    release = DummyRelease([], experiment="cms")
    with patch("cernopendata.modules.releases.validations.recid.db") as mock_db:
        mock_db.session.query.return_value.filter.return_value.scalar.side_effect = [
            max_release,
            max_registered,
            max_numeric,
        ]
        assert validator.next_recid_start(release) == expected


def test_validator_recid_fix_numeric_collision():
    validator = ValidRecid()
    release = DummyRelease([{"recid": "CMS-1"}, {"recid": "CMS-42"}])
    with patch.object(validator, "next_recid_start", return_value=100), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ), patch.object(validator, "_numeric_collisions", return_value=[(0, "CMS-1", "1")]):
        errors = validator.fix(release)

    assert errors == []
    assert [record["recid"] for record in release.records] == ["CMS-100", "CMS-42"]
    assert release.max_recid == 100


def test_validator_recid_numeric_collision():
    validator = ValidRecid()
    release = DummyRelease(
        [{"recid": "atlas-1"}, {"recid": "atlas-2"}], experiment="atlas"
    )
    with patch(
        "cernopendata.modules.releases.validations.recid.PersistentIdentifier"
    ) as mock_pid:
        mock_pid.query.filter.return_value.all.return_value = [MagicMock(pid_value="1")]
        collisions = validator._numeric_collisions(release)
    assert collisions == [(0, "atlas-1", "1")]
