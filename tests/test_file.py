# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2021 CERN.
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

import json

import pytest
from invenio_files_rest.models import Location
from invenio_indexer.api import RecordIndexer

from cernopendata.modules.fixtures.cli import create_record
from cernopendata.modules.records.utils import record_file_page


def test_file_index(app, database, search):
    """Checking that records can be inserted"""
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
    }
    location = Location(name="local", uri="var/data", default=True)
    database.session.add(location)
    record = create_record(data, False)

    indexer = RecordIndexer()
    done = indexer.index(record)

    assert done["_index"] == "records-record-v1.0.0"
    with app.test_request_context("/group=1"):
        req = record_file_page(
            None,
            record,
        )
        response = json.loads(req.response[0])
    assert response["files"][0]["uri"] == "root://foo/bar"
