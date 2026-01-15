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

"""CERN Open Data Release views."""

import json
from datetime import datetime

import requests
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request
from flask_login import current_user, login_required

from .api import Release
from .models import ReleaseStatus
from .utils import curator_experiments

blueprint = Blueprint(
    "cernopendata_curate",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@blueprint.route("/releases/api/list/<experiment>", methods=["GET"])
@login_required
def list_releases(experiment=None):
    """Return list of releases."""
    if not Release.validate_experiment(experiment):
        abort(404)
    if experiment not in curator_experiments()["curator_experiments"]:
        abort(403)
    releases = Release.list_releases(experiment)

    # Serialize
    def serialize_last_update(event):
        return {
            "status": event.status,
            "timestamp": event.timestamp.isoformat(),
            "user": event.user.email if event.user else None,
        }

    return jsonify(
        [
            {
                "id": r.id,
                "name": r.name,
                "discussion": r.discussion_url,
                "status": r.status,
                "last_update": (
                    serialize_last_update(r.history_events[-1])
                    if r.history_events
                    else None
                ),
                "num_records": r.num_records,
                "num_docs": r.num_docs,
                "num_errors": r.num_errors,
                "num_files": r.num_files,
            }
            for r in releases
        ]
    )


@blueprint.route("/releases/<experiment>")
@login_required
def release_view(experiment=None):
    """Landing page for the curation process."""
    if not Release.validate_experiment(experiment):
        abort(404)

    if experiment not in curator_experiments()["curator_experiments"]:
        abort(403)
    return render_template(
        "cernopendata_pages/releases.html", experiment=experiment.upper()
    )


@blueprint.route("/releases/<experiment>", methods=["POST"])
@login_required
def release_upload(experiment):
    """Upload a new release into the system."""
    if not Release.validate_experiment(experiment):
        abort(404)

    if experiment not in curator_experiments()["curator_experiments"]:
        abort(403)
    source = request.form.get("source")

    if source == "file":
        file = request.files.get("file")
        if not file.filename.endswith(".json"):
            return jsonify({"error": "Only JSON files are allowed"}), 400

        try:
            payload = json.load(file)
        except Exception as e:
            return jsonify({"error": "Invalid JSON", "details": str(e)}), 400
        release_name = file.filename.rsplit("/", 1)[-1]

    elif source == "url":
        url = request.form.get("url")
        if not url:
            abort(400, "Missing URL")

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        release_name = url.rsplit("/", 1)[-1]

    else:
        abort(400, "Invalid source")
    if isinstance(payload, dict):
        # In case we are reading from the cernopandata api, where the record is in the 'metadata' field
        if "metadata" in payload:
            for field in "_files", "_bucket", "bucket", "_file_indices":
                if field in payload["metadata"]:
                    del payload["metadata"][field]
            payload = [payload["metadata"]]
        else:
            payload = [payload]
    release = Release.create(
        records=payload,
        experiment=experiment,
        current_user=current_user,
        name=release_name,
    )

    flash(f"Release {release._metadata.id} created.", "success")

    return render_template(
        "cernopendata_pages/releases.html", experiment=experiment.upper()
    )


@blueprint.route("/releases/<experiment>/<int:release_id>")
def release_detail(experiment, release_id):
    """Get the details of a release."""
    release = _get_release(experiment, release_id)
    return render_template(
        "cernopendata_pages/release_details.html",
        release=release,
        experiment=experiment,
        current_year=datetime.utcnow().year,
    )


# @blueprint.route(
#    "/releases/<experiment>/<int:release_id>/generate_doi",
#    methods=["POST"],
# )
# def generate_doi(experiment, release_id):
#    """Generate DOI for the records inside a release. TODO."""
#    release = _get_release(
#        experiment, release_id, lock=True, status=ReleaseStatus.DRAFT
#    )##
#
#    if release.valid_doi:
#        abort(400, "RECIDs already generated")#
#
#    release.generate_doi()
#    db.session.add(release)
#    db.session.commit()
#
#    flash(f"Recid created for records in release {release.id}.", "success")
#
#    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/delete",
    methods=["POST"],
)
@login_required
def delete_release(experiment, release_id):
    """Delete a release."""
    release = _get_release(experiment, release_id)

    release.delete()

    flash("Release deleted successfully.", "success")

    return redirect(f"/releases/{experiment}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/update_records",
    methods=["POST"],
)
@login_required
def update_records(experiment, release_id):
    """Update the records of a release."""
    # Get JSON string from form
    import sys

    print("HELLO", file=sys.stderr)
    data = request.get_json()
    if not data["records"]:
        abort(400, "No records provided")

    if not isinstance(data["records"], list):
        raise ValueError("Records must be a list")

    release = _get_release(experiment, release_id, lock=ReleaseStatus.EDITING)
    release.update_records(data["records"], current_user)

    flash("Records updated successfully.", "success")
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/deploy",
    methods=["POST"],
)
@login_required
def deploy_release(experiment, release_id):
    """Insert the objects defined in the release in the current system."""
    release = _get_release(
        experiment, release_id, status=ReleaseStatus.READY, lock=ReleaseStatus.DEPLOYING
    )
    schema = "local://records/record-v1.0.0.json"
    try:
        release.deploy(schema, current_user)
        flash("Release deployed successfully.", "success")

    except Exception as e:
        flash(f" :( Error deploying the release {e}", "error")

    return redirect(f"/releases/{experiment}/{release_id}")


def _get_release(experiment, release_id, lock=False, status=None):
    """Given an experiment and a relese number, return the release object."""
    if not Release.validate_experiment(experiment):
        abort(404)
    if experiment not in curator_experiments()["curator_experiments"]:
        abort(403)

    release = Release.get(experiment, release_id)

    if not release:
        abort(404)
    if status and not release.is_status(status):
        abort(409)
    if lock and not release.lock(status, lock, current_user):
        abort(409)

    return release


@blueprint.route("/releases/<experiment>/<int:release_id>/rollback", methods=["POST"])
@login_required
def rollback(experiment, release_id):
    """Remove the records from the instance."""
    release = _get_release(experiment, release_id, status=ReleaseStatus.DEPLOYED)

    release.rollback(current_user)

    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route("/releases/<experiment>/<int:release_id>/publish", methods=["POST"])
@login_required
def publish(experiment, release_id):
    """Publish the records: put them in the search, and remove the box saying that they were work in progress."""
    release = _get_release(experiment, release_id, status=ReleaseStatus.DEPLOYED)

    release.publish(current_user)
    flash("Release published!")
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/bulk_records/preview",
    methods=["POST"],
)
@login_required
def bulk_edit_records_preview(experiment, release_id):
    """Preview the changes that a bulk action would do."""
    payload = request.get_json()
    updates = payload.get("updates", {})

    release = _get_release(experiment, release_id)
    diffs = release.bulk_preview(updates)
    return {
        "total_records": len(release.records),
        "diffed_records": len(diffs),
        "diffs": diffs,
    }


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/bulk_records/apply",
    methods=["POST"],
)
@login_required
def bulk_edit_records_apply(experiment, release_id):
    """Perform a bulk update on all the records."""
    updates = None
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if "updates" in data:
            updates = data["updates"]
    elif "updates" in request.form:
        try:
            updates = json.loads(request.form["updates"])
        except ValueError:
            abort(400, "Invalid JSON in upload")

    if not updates:
        abort(400, "Missing updates")

    release = _get_release(experiment, release_id, lock=ReleaseStatus.EDITING)
    diff = release.bulk_update(updates, current_user)

    flash(
        f"Bulk edit applied to " f"{diff} records.",
        "success",
    )
    if request.is_json:
        return jsonify({"status": "ok"})
    else:
        return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/fix_checks",
    methods=["POST"],
)
@login_required
def fix_checks(experiment, release_id):
    """Fix automatically part of the metadata of the release."""
    release = _get_release(
        experiment,
        release_id,
        status=ReleaseStatus.DRAFT,
        lock=ReleaseStatus.EDITING,
    )
    release.fix_checks(current_user)

    return redirect(f"/releases/{experiment}/{release_id}")
