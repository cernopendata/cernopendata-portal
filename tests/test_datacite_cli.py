# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Open Data Portal; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

from unittest.mock import MagicMock

from cernopendata.modules.datacite.cli import register, test_serialisation, update


def test_test_serialisation_outputs_validated_doc(app, cli_runner, mocker):
    mock_pid = mocker.patch("cernopendata.modules.datacite.cli.PersistentIdentifier")
    mock_pid.get.return_value = MagicMock(object_uuid="some-uuid")
    mock_record_cls = mocker.patch("cernopendata.modules.datacite.cli.Record")
    mock_record_cls.get_record.return_value = {"recid": 1, "doi": "10.1234/TEST"}
    mock_validate = mocker.patch(
        "cernopendata.modules.datacite.cli.validate_record",
        return_value="<resource/>",
    )

    result = cli_runner.invoke(test_serialisation, ["--recid", "1"], obj=app)

    assert result.exit_code == 0
    assert "<resource/>" in result.output
    mock_pid.get.assert_called_once_with("recid", "1")
    mock_record_cls.get_record.assert_called_once_with("some-uuid")
    mock_validate.assert_called_once_with({"recid": 1, "doi": "10.1234/TEST"})


def test_register_calls_register_record_doi_and_echoes_doi(app, cli_runner, mocker):
    mock_pid = mocker.patch("cernopendata.modules.datacite.cli.PersistentIdentifier")
    mock_pid.get.return_value = MagicMock(object_uuid="some-uuid")
    mock_record_cls = mocker.patch("cernopendata.modules.datacite.cli.Record")
    record = {"recid": 1, "doi": "10.1234/TEST"}
    mock_record_cls.get_record.return_value = record
    mock_register = mocker.patch(
        "cernopendata.modules.datacite.cli.register_record_doi"
    )
    mock_db = mocker.patch("cernopendata.modules.datacite.cli.db")

    result = cli_runner.invoke(register, ["--recid", "1"], obj=app)

    assert result.exit_code == 0
    assert "Record registered with DOI 10.1234/TEST" in result.output
    mock_register.assert_called_once_with(record)
    mock_db.session.commit.assert_called_once()


def test_update_validates_and_updates_when_doi_registered(app, cli_runner, mocker):
    mock_pid = mocker.patch("cernopendata.modules.datacite.cli.PersistentIdentifier")
    mock_pid.get.return_value = MagicMock(object_uuid="some-uuid")
    mock_record_cls = mocker.patch("cernopendata.modules.datacite.cli.Record")
    record = {"recid": 1, "doi": "10.1234/TEST"}
    mock_record_cls.get_record.return_value = record
    mock_provider = MagicMock()
    mock_wrapper = mocker.patch(
        "cernopendata.modules.datacite.cli.DataCiteProviderWrapper"
    )
    mock_wrapper.get.return_value = mock_provider
    mock_validate = mocker.patch(
        "cernopendata.modules.datacite.cli.validate_record",
        return_value="<resource/>",
    )
    mock_db = mocker.patch("cernopendata.modules.datacite.cli.db")
    app.config["PIDSTORE_LANDING_BASE_URL"] = "https://opendata.cern.ch/record"

    result = cli_runner.invoke(update, ["--recid", "1"], obj=app)

    assert result.exit_code == 0
    assert "Record with DOI 10.1234/TEST updated in DataCite" in result.output
    mock_validate.assert_called_once_with(record)
    mock_provider.update.assert_called_once_with(
        url="https://opendata.cern.ch/record/1", doc="<resource/>"
    )
    mock_db.session.commit.assert_called_once()
