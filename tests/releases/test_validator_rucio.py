import os
from datetime import datetime

import pytest

from cernopendata.modules.releases.validations.rucio import RucioDatasets


class DummyRelease:
    def __init__(self, records, experiment="cms"):
        self.records = records
        self.experiment = experiment


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(
        RucioDatasets, "_get_config_errors", lambda self, experiment: []
    )
    monkeypatch.setattr(
        RucioDatasets, "_setup_environment", lambda self, experiment: None
    )


def test_config_present(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("RUCIO_HOME", "")
    monkeypatch.setenv("X509_USER_PROXY", "")
    rucio_home = tmp_path / "atlas" / "rucio"
    rucio_home.mkdir(parents=True)
    proxy = tmp_path / ".globus" / "atlas" / "userproxy.pem"
    proxy.parent.mkdir(parents=True)
    proxy.write_text("proxy")

    validator = RucioDatasets()
    assert validator._get_config_errors("atlas") == []

    validator._setup_environment("atlas")
    assert os.environ["RUCIO_HOME"] == str(rucio_home)
    assert os.environ["X509_USER_PROXY"] == str(proxy)


def test_config_missing_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("RUCIO_HOME", raising=False)
    monkeypatch.delenv("X509_USER_PROXY", raising=False)
    rucio_home = tmp_path / "cms" / "rucio"
    proxy = tmp_path / ".globus" / "cms" / "userproxy.pem"

    errors = RucioDatasets()._get_config_errors("cms")

    assert errors == [
        f"Missing Rucio configuration for cms (expected {rucio_home})",
        f"Missing X509 proxy for cms (expected {proxy})",
    ]
    assert "RUCIO_HOME" not in os.environ
    assert "X509_USER_PROXY" not in os.environ


@pytest.mark.parametrize("config_errors, expected", [([], True), (["error"], False)])
def test_fixable(monkeypatch, config_errors, expected):
    monkeypatch.setattr(
        RucioDatasets, "_get_config_errors", lambda self, experiment: config_errors
    )

    assert RucioDatasets().fixable(DummyRelease(records=[])) is expected


# -------------------------
# validate
# -------------------------
def test_validate_detects_missing_files(configured):
    release = DummyRelease(
        records=[
            {"rucio_dataset": "scope:dataset1"},
        ]
    )

    validator = RucioDatasets()
    errors = validator.validate(release)

    assert len(errors) == 1
    assert "record 1" in errors[0]


def test_validate_ok_when_files_present(configured):
    release = DummyRelease(
        records=[
            {"rucio_dataset": "scope:dataset1", "files": []},
        ]
    )

    validator = RucioDatasets()
    assert validator.validate(release) == []


def test_validate_reports_config_errors(monkeypatch):
    monkeypatch.setattr(
        RucioDatasets, "_get_config_errors", lambda self, experiment: ["not configured"]
    )
    release = DummyRelease(records=[{"rucio_dataset": "scope:dataset1"}])

    assert RucioDatasets().validate(release) == ["not configured"]


# -------------------------
# _get_files_from_rucio_dataset
# -------------------------
@pytest.mark.parametrize("experiment", ["cms", "atlas"])
def test_get_files_from_rucio_dataset_success(experiment):
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

    files = validator._get_files_from_rucio_dataset(
        FakeRucioClient(), "scope:dataset", experiment
    )

    assert len(files) == 1
    assert files[0]["checksum"] == "adler32:1234"
    assert files[0]["key"] == "file.root"
    assert files[0]["size"] == 100
    assert (
        files[0]["uri"]
        == f"root://eospublic.cern.ch//eos/opendata/{experiment}/sub/file.root"
    )


def test_get_files_from_rucio_dataset_empty():
    validator = RucioDatasets()

    class FakeRucioClient:
        def list_files(self, scope, name):
            return []

    files = validator._get_files_from_rucio_dataset(
        FakeRucioClient(), "scope:dataset", "cms"
    )

    assert files == []


# -------------------------
# fix
# -------------------------
def test_fix_expands_rucio_dataset(configured, monkeypatch):
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
    assert record["date_published"] == str(datetime.now().year)
    assert record["files"][0]["key"] == "file.root"
    assert record["distribution"]["number_files"] == 1
    assert record["type"] == {"primary": "Dataset"}


# -------------------------
# fix no-op case
# -------------------------
def test_fix_does_nothing_without_rucio(configured, monkeypatch):
    validator = RucioDatasets()

    release = DummyRelease(records=[{"files": []}])

    class FakeClient:
        def list_files(self, client, did):
            return []

    from cernopendata.modules.releases.validations import rucio

    monkeypatch.setattr(rucio, "DIDClient", lambda: FakeClient())

    errors = validator.fix(release)

    assert errors == []
