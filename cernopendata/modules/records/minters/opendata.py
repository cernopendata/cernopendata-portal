# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2026 CERN.
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
"""Generic minter for opendata records. It does a concept mint, and then one per version."""
from invenio_oaiserver.provider import OAIIDProvider


def cernopendata_generic_minter(
    record_uuid, data, pid_type, id_field, provider, oai=False
):
    """Mint deposit's PID."""
    version = f"v{data['version']}"
    new_entry = provider.create(
        object_type="rec",
        pid_type=pid_type,
        object_uuid=record_uuid,
        pid_value=f"{data[id_field]}-{version}",
    )
    if oai:
        data["pids"] = {"oai": {"id": f"oai:cernopendata.cern:{data[id_field]}"}}
        OAIIDProvider.create(
            object_type="rec",
            object_uuid=record_uuid,
            pid_value=f"oai:cernopendata.cern:{data[id_field]}-{version}",
        )

    # The first version also registers the concept
    if version == "v1":
        provider.create(
            object_type="rec",
            pid_type=pid_type,
            object_uuid=record_uuid,
            pid_value=str(data[id_field]),
        )
        if oai:
            OAIIDProvider.create(
                object_type="rec",
                object_uuid=record_uuid,
                pid_value=f"oai:cernopendata.cern:{data[id_field]}",
            )
    return new_entry.pid
