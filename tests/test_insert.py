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

import pytest
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDAlreadyExists

from cernopendata.modules.fixtures.cli import create_glossary_term


def test_insert(app, database, search):
    """Checking that records can be inserted"""
    data = {
        "anchor": "dummy_test",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
    }
    record = create_glossary_term(data, True)

    indexer = RecordIndexer()
    done = indexer.index(record)

    assert done["_index"] == "records-glossary-term-v1.0.0"


def test_insert_twice(app, database, search):
    """Checking what happens if the same record is inserted twice"""
    data = {
        "anchor": "dummy_test_duplicate",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
    }
    record1 = create_glossary_term(data, skip_files=True)

    indexer = RecordIndexer()
    indexer.index(record1)
    with pytest.raises(PIDAlreadyExists):
        record2 = create_glossary_term(data, skip_files=True)
        indexer.index(record2)
        print("This was not supposed to work. It is a duplicate :(")
