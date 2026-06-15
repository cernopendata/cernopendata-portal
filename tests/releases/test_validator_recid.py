from unittest.mock import patch

from cernopendata.modules.releases.models import ReleaseStatus
from cernopendata.modules.releases.validations.recid import ValidRecid


class DummyRelease:
    def __init__(self, records, experiment="CMS", status="DRAFT", max_recid=0):
        self.records = records
        self.experiment = experiment
        self.status = ReleaseStatus[status].value
        self.max_recid = max_recid


def test_fix_assigns_recid():
    validator = ValidRecid()
    release = DummyRelease([{"title": "no recid"}])
    with patch.object(validator, "next_recid_start", return_value=6), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ):
        errors = validator.fix(release)
    assert errors == []
    assert release.records[0]["recid"] == "CMS-6"
    assert release.max_recid == 6


def test_fix_keeps_existing_recid():
    validator = ValidRecid()
    release = DummyRelease([{"recid": "CMS-42"}])
    with patch.object(validator, "next_recid_start", return_value=6), patch.object(
        validator, "_duplicate_pids", return_value=[]
    ):
        validator.fix(release)
    assert release.records[0]["recid"] == "CMS-42"


def test_fix_reassigns_duplicate_recid():
    validator = ValidRecid()
    release = DummyRelease([{"recid": "CMS-7"}])
    with patch.object(validator, "next_recid_start", return_value=11), patch.object(
        validator, "_duplicate_pids", return_value=["CMS-7"]
    ):
        validator.fix(release)
    assert release.records[0]["recid"] == "CMS-11"
