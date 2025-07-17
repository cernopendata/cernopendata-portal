# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2018 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Sitemap generation for CERN Open Data Portal."""
import math

import arrow
from flask import current_app, url_for
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata

from .config import CERNOPENDATA_SITEMAP_PAGE_SIZE


def _sitemapdtformat(dt):
    """Convert a datetime to a W3 Date and Time format.

    Converts the date to a minute-resolution datetime timestamp with a special
    UTC designator 'Z'. See more information at
    https://www.w3.org/TR/NOTE-datetime.
    """
    adt = arrow.Arrow.fromdatetime(dt).to("utc")
    return adt.format("YYYY-MM-DDTHH:mm:ss") + "Z"


def _url_generator_query(doc_types, offset, limit):
    """Returns an Sqlalchemy query for fetching urls."""
    q = (
        db.session.query(PersistentIdentifier, RecordMetadata)
        .join(RecordMetadata, RecordMetadata.id == PersistentIdentifier.object_uuid)
        .filter(
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_type.in_(doc_types),
        )
    )

    # allow offset and limits for pagination
    if limit is not None:
        q = q.offset(offset)
    if limit is not None:
        q = q.limit(limit)

    return q


def yield_urls(doc_types, offset=None, limit=None):
    """Generate the records links from `url_generator_query`."""
    query = _url_generator_query(doc_types, offset, limit)

    scheme = current_app.config["CERNOPENDATA_SITEMAP_URL_SCHEME"]
    for pid, rm in query.all():
        yield {
            "loc": url_for(
                f"invenio_records_ui.{pid.pid_type}",
                pid_value=pid.pid_value,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(rm.updated),
        }


def sitemap_page_urls(doc_types):
    """Count the number of urls from `url_generator_query`."""
    query = _url_generator_query(doc_types, None, None)
    pages = math.ceil(query.count() / CERNOPENDATA_SITEMAP_PAGE_SIZE)

    scheme = current_app.config["CERNOPENDATA_SITEMAP_URL_SCHEME"]

    for i in range(pages):
        yield url_for("cernopendata_sitemap.sitemap_page", _scheme=scheme, page=i)
