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

"""cernopendata-query-parser test."""
from invenio_search.engine import dsl

from cernopendata.config import _query_parser_and


def _create_query(term):
    # Defines the skeleton of a query
    return dsl.query.Bool(
        must=[
            dsl.query.QueryString(
                default_operator="AND",
                fields=["title.tokens^2", "*"],
                query=term,
                type="cross_fields",
            )
        ],
        must_not=[dsl.query.Match(distribution__availability="ondemand")],
    )


def test_cernopendata_query_parser(app):
    with app.test_request_context("/"):
        assert _query_parser_and("/Btau") == _create_query("\\/Btau")
        assert _query_parser_and('"/Btau"') == _create_query('"\\/Btau"')
        assert _query_parser_and("/btau AND CMS") == _create_query("\\/btau AND CMS")
        assert _query_parser_and('"/btau" AND CMS') == _create_query(
            '"\\/btau" AND CMS'
        )
        assert _query_parser_and("CMS AND /btau") == _create_query("CMS AND \\/btau")

    with app.test_request_context("/?ondemand=true"):
        assert _query_parser_and("CMS AND /btau") == dsl.query.QueryString(
            default_operator="AND",
            fields=["title.tokens^2", "*"],
            query="CMS AND \\/btau",
            type="cross_fields",
        )
