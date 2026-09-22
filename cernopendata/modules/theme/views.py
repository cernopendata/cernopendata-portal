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

"""CERN Open Data theme."""

import operator

from flask import Blueprint

from cernopendata.modules.records.utils import (
    serialize_record as utils_serialize_record,
)

blueprint = Blueprint(
    "cernopendata_theme",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@blueprint.app_template_filter("get_record_title")
def get_record_title(id, type="recid"):
    """Fetches record title by id."""
    from invenio_pidstore.errors import PIDDoesNotExistError
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records.api import Record

    try:
        pid = PersistentIdentifier.get(type, id)
    except PIDDoesNotExistError:
        return None
    record = Record.get_record(pid.object_uuid)
    return record.get("title", "")


@blueprint.app_template_global("entry_versions")
def entry_versions(pid_type, entry_id, current_uuid=None):
    """Return every version of an entry, sorted from the oldest one.

    `entry_id` is the identifier without the version suffix, and `current_uuid`
    the id of the record being displayed, used to flag which version that is.
    The versions are discovered from the PIDs, so the full list is returned no
    matter which version is being displayed. Each one is reported with the date
    its record was created, which is when that version appeared on the portal.
    Versions whose record is gone are skipped, so that a broken version does
    not hide the rest of them.
    """
    import re

    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records.api import Record
    from sqlalchemy.exc import NoResultFound

    # The '_' of a slug is a wildcard for LIKE, so the suffix is checked again
    # below to discard the entries that only look like a version of this one.
    candidates = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_type == pid_type,
        PersistentIdentifier.pid_value.like(f"{entry_id}-v%"),
    ).all()

    versions = []
    for pid in candidates:
        match = re.fullmatch(rf"{re.escape(entry_id)}-v(\d+)", pid.pid_value)
        if not match:
            continue
        try:
            record = Record.get_record(pid.object_uuid)
        except NoResultFound:
            continue
        versions.append(
            {
                "index": int(match.group(1)),
                "pid_value": pid.pid_value,
                "created": record.created,
                "is_current": str(pid.object_uuid) == str(current_uuid),
            }
        )

    return sorted(versions, key=lambda version: version["index"])


@blueprint.app_template_filter("get_first_file")
def get_first_file(file_list):
    """Fetches first file from a list."""
    keys = [f.get("key") for f in file_list if f.get("key", "").endswith(".ig")]
    if keys:
        return keys[0]


@blueprint.app_template_filter("sort_multi")
def sort_multi(lst, *operators):
    """Sorts list by multiple fields."""
    lst.sort(key=operator.itemgetter(*operators))
    return lst


@blueprint.app_template_filter("get_year")
def get_year(year):
    """Returns current year."""
    import datetime

    now = datetime.datetime.now()
    return now.year


@blueprint.app_template_filter("serialize_record")
def serialize_record(record, pid, serializer, module=None, throws=True, **kwargs):
    """Serialize record according to the passed serializer."""
    return utils_serialize_record(
        record, pid, serializer, module=module, throws=throws, **kwargs
    )
