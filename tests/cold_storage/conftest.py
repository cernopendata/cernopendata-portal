import os

import pytest
from invenio_files_rest.models import Location

from cernopendata.cold_storage.cli import location
from cernopendata.modules.fixtures.cli import create_record

from .utils import build_record_with_files


@pytest.fixture(scope="module")
def storage_paths(tmp_path_factory):
    """
    Provides hot and cold storage paths within a temporary directory.
    """
    base_tmp_path = tmp_path_factory.mktemp("cold_storage_module_base")
    hot_path = base_tmp_path / "hot_storage"
    cold_path = base_tmp_path / "cold_storage"
    os.makedirs(hot_path, exist_ok=True)
    os.makedirs(cold_path, exist_ok=True)
    return hot_path, cold_path


@pytest.fixture(scope="module")
def setup_location(cli_runner, app, database, storage_paths):
    """Sets up the storage locations in the database and via CLI."""
    hot_path, cold_path = storage_paths
    manager_class = "cernopendata.cold_storage.transfer.cp.TransferManager"

    record_location = Location(name="local", uri=str(hot_path), default=True)
    database.session.add(record_location)
    database.session.commit()

    result = cli_runner.invoke(
        location,
        [
            "add",
            "--cold-path",
            str(cold_path),
            "--hot-path",
            str(hot_path),
            "--manager-class",
            manager_class,
        ],
        obj=app,
    )
    assert result.exit_code == 0
    assert "Location added with ID" in result.output


@pytest.fixture
def record_factory(app, database, storage_paths, setup_location):
    """Creates a record"""

    def _create(record_data):
        record_id, hot_paths, cold_paths, record_dict = build_record_with_files(
            app, storage_paths, record_data
        )
        record = create_record(record_dict, False)
        record.commit()
        database.session.commit()
        return {
            "id": record_id,
            "hot_paths": hot_paths,
            "cold_paths": cold_paths,
            "record_obj": record,
        }

    return _create


@pytest.fixture(scope="module")
def staged_record(app, database):
    if not Location.query.filter_by(name="local").first():
        database.session.add(Location(name="local", uri="var/data", default=True))

    data = {
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/record-v1.0.0.json"
        ),
        "recid": "1114",
        "date_published": "2024",
        "experiment": ["ALICE"],
        "publisher": "CERN Open Data Portal",
        "title": "Dummy file",
        "type": {
            "primary": "Dataset",
            "secondary": ["Derived"],
        },
        "files": [
            {"checksum": "adler32:9719fd6a", "size": 1053, "uri": "root://foo/bar"}
        ],
        "_availability_details": {"on demand": 1},
        "distribution": {
            "size": 1053,
            "formats": ["root"],
            "number_files": 1,
            "number_events": 37,
        },
    }
    record = create_record(data, False)
    database.session.commit()
    data.update({"record_id": record.id})
    return data
