from unittest.mock import MagicMock

import pytest
from invenio_pidstore.errors import PIDDoesNotExistError

from cernopendata.modules.datacite.utils import register_record_doi, validate_record


def test_validate_record_returns_serialized_doc(mocker):
    mock_serializer_cls = mocker.patch(
        "cernopendata.modules.datacite.utils.DataCiteSerializer"
    )
    mock_schema43 = mocker.patch("cernopendata.modules.datacite.utils.schema43")

    mock_doc = {"titles": [{"title": "Test"}]}
    mock_serializer_cls.return_value.dump.return_value = mock_doc
    mock_schema43.tostring.return_value = "<resource/>"

    record = {"recid": 1, "title": "Test"}
    result = validate_record(record)

    mock_serializer_cls.return_value.dump.assert_called_once_with(record)
    mock_schema43.validate.assert_called_once_with(mock_doc)
    mock_schema43.tostring.assert_called_once_with(mock_doc)
    assert result == "<resource/>"


def test_validate_record_propagates_schema_errors(mocker):
    mocker.patch(
        "cernopendata.modules.datacite.utils.DataCiteSerializer"
    ).return_value.dump.return_value = {}
    mock_schema43 = mocker.patch("cernopendata.modules.datacite.utils.schema43")
    mock_schema43.validate.side_effect = ValueError("required field missing")

    with pytest.raises(ValueError, match="required field missing"):
        validate_record({"recid": 1})


def test_register_record_doi_reuses_existing_provider(mocker):
    mock_provider = MagicMock()
    mock_wrapper = mocker.patch(
        "cernopendata.modules.datacite.providers.DataCiteProviderWrapper"
    )
    mock_wrapper.get.return_value = mock_provider

    mocker.patch(
        "cernopendata.modules.datacite.utils.validate_record",
        return_value="<resource/>",
    )
    mock_current_app = mocker.patch("cernopendata.modules.datacite.utils.current_app")
    mock_current_app.config = {
        "PIDSTORE_LANDING_BASE_URL": "https://opendata.cern.ch/record"
    }

    record_data = {"doi": "10.1234/TEST", "recid": 42, "experiment": "CMS"}
    register_record_doi(record_data)

    mock_wrapper.get.assert_called_once_with(pid_value="10.1234/TEST", pid_type="doi")
    mock_wrapper.create.assert_not_called()
    mock_provider.register.assert_called_once_with(
        url="https://opendata.cern.ch/record/42", doc="<resource/>"
    )


def test_register_record_doi_creates_provider_when_missing(mocker):
    mock_provider = MagicMock()
    mock_wrapper = mocker.patch(
        "cernopendata.modules.datacite.providers.DataCiteProviderWrapper"
    )
    mock_wrapper.get.side_effect = PIDDoesNotExistError("doi", "10.1234/NEW")
    mock_wrapper.create.return_value = mock_provider

    mocker.patch(
        "cernopendata.modules.datacite.utils.validate_record",
        return_value="<resource/>",
    )
    mock_current_app = mocker.patch("cernopendata.modules.datacite.utils.current_app")
    mock_current_app.config = {
        "PIDSTORE_LANDING_BASE_URL": "https://opendata.cern.ch/record"
    }

    record_data = {"doi": "10.1234/NEW", "recid": 7, "experiment": "CMS"}
    register_record_doi(record_data)

    mock_wrapper.create.assert_called_once_with(
        pid_value="10.1234/NEW", experiment="CMS"
    )
    mock_provider.register.assert_called_once_with(
        url="https://opendata.cern.ch/record/7", doc="<resource/>"
    )
