import pytest

from cernopendata.modules.releases.validations.rucio import RucioDatasets


class DummyRelease:
    def __init__(self, records):
        self.records = records


# -------------------------
# validate
# -------------------------
def test_validate_detects_missing_files():
    release = DummyRelease(
        records=[
            {"rucio_dataset": "scope:dataset1"},
        ]
    )

    validator = RucioDatasets()
    errors = validator.validate(release)

    assert len(errors) == 1
    assert "record 0" in errors[0]


def test_validate_ok_when_files_present():
    release = DummyRelease(
        records=[
            {"rucio_dataset": "scope:dataset1", "files": []},
        ]
    )

    validator = RucioDatasets()
    assert validator.validate(release) == []


# -------------------------
# _get_files_from_rucio_dataset
# -------------------------
def test_get_files_from_rucio_dataset_success(monkeypatch):
    validator = RucioDatasets()

    class FakeRucioClient:
        def list_files(self, scope, name):
            return [
                {
                    "adler32": "1234",
                    "name": "sub/file.root",
                    "bytes": 100,
                }
            ]

    files = validator._get_files_from_rucio_dataset(FakeRucioClient(), "scope:dataset")

    assert len(files) == 1
    assert files[0]["checksum"] == "adler32:1234"
    assert files[0]["key"] == "file.root"
    assert files[0]["size"] == 100
    assert files[0]["uri"].startswith("root://eospublic.cern.ch")


def test_get_files_from_rucio_dataset_empty(monkeypatch):
    validator = RucioDatasets()

    class FakeRucioClient:
        def list_files(self, scope, name):
            return []

    files = validator._get_files_from_rucio_dataset(FakeRucioClient(), "scope:dataset")

    assert files == []


# -------------------------
# fix
# -------------------------
def test_fix_expands_rucio_dataset(monkeypatch):
    validator = RucioDatasets()

    release = DummyRelease(
        records=[
            {
                "rucio_dataset": "cms:/type/2017/NANOAODSIM",
            }
        ]
    )

    # patch file expansion function
    #    def fake_get_files(self, client, did):
    #        return

    class FakeClient:
        def list_files(self, client, did):
            return [
                {
                    "checksum": "adler32:1",
                    "size": 10,
                    "name": "root://eos/file.root",
                }
            ]

    from cernopendata.modules.releases.validations import rucio

    monkeypatch.setattr(rucio, "DIDClient", lambda: FakeClient())

    errors = validator.fix(release)

    assert errors == []

    record = release.records[0]

    assert record["title"] == "/type/2017/NANOAODSIM"
    assert record["date_published"] == "2026"
    assert record["files"][0]["key"] == "file.root"
    assert record["distribution"]["number_files"] == 1
    assert record["type"]["primary"] == "Dataset"


# -------------------------
# fix no-op case
# -------------------------
def test_fix_does_nothing_without_rucio(monkeypatch):
    validator = RucioDatasets()

    release = DummyRelease(records=[{"files": []}])

    class FakeClient:
        def list_files(self, client, did):
            return []

    from cernopendata.modules.releases.validations import rucio

    monkeypatch.setattr(rucio, "DIDClient", lambda: FakeClient())

    errors = validator.fix(release)

    assert errors == []
