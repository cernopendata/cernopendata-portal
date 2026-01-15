# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2024 CERN.
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

"""CERN Open Data Release utils."""
from flask import current_app
from flask_login import current_user
from invenio_accounts import current_accounts
from invenio_accounts.views.rest import role_to_dict
from invenio_db import db
from invenio_oauthclient.contrib.keycloak.helpers import get_user_info
from invenio_oauthclient.models import RemoteAccount


def user_info_with_cern_roles(remote, resp):
    """Return a user with the roles from the SSO application."""
    token_user_info, user_info = get_user_info(remote, resp)
    username = token_user_info["sub"]
    email = token_user_info["email"]
    # cern_person_id might be missing for non-CERN users (EduGain)
    identity_id = token_user_info.get("cern_person_id") or username
    preferred_language = user_info.get("cern_preferred_language", "en").lower()
    client_id = current_app.config["CERN_APP_CREDENTIALS"]["consumer_key"]
    user = current_accounts.datastore.get_user_by_email(email)
    remote_user = RemoteAccount.get(user.id, client_id)
    if remote_user:
        remote_user.extra_data["cern_roles"] = token_user_info["cern_roles"]
        db.session.commit()
        db.session.commit()
    return {
        "user": {
            "active": True,
            "email": email,
            "profile": {
                "affiliations": user_info.get("home_institute", ""),
                "full_name": user_info.get(
                    "name", token_user_info.get("name", "")
                ),  # user_info might be missing
                "username": username,
            },
            "prefs": {
                "visibility": "public",
                "email_visibility": "public",
                "locale": preferred_language,
            },
        },
        "external_id": identity_id,
        "external_method": remote.name,
        "cern_roles": token_user_info.get("cern_roles", []),
    }


def user_payload_with_cern_roles(user):
    """Parse user payload."""
    fmt_last_login_at = None
    if user.login_info and user.login_info.last_login_at:
        fmt_last_login_at = user.login_info.last_login_at.isoformat()
    client_id = current_app.config["CERN_APP_CREDENTIALS"]["consumer_key"]
    remote_user = RemoteAccount.get(user.id, client_id)
    return {
        "id": user.id,
        "email": user.email,
        "confirmed_at": user.confirmed_at.isoformat() if user.confirmed_at else None,
        "last_login_at": fmt_last_login_at,
        "roles": [role_to_dict(role) for role in user.roles],
        "cern_roles": remote_user.extra_data["cern_roles"],
    }


def curator_experiments():
    """Return experiments where the user is curator."""
    exps = []
    if current_user.is_authenticated:
        client_id = current_app.config["CERN_APP_CREDENTIALS"]["consumer_key"]
        remote_user = RemoteAccount.get(current_user.id, client_id)
        roles = remote_user.extra_data.get("cern_roles", [])
        exps = [r[:-8] for r in roles if r.endswith("-curator")]
    return dict(curator_experiments=exps)
