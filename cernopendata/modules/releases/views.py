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
import os
from datetime import datetime
from pathlib import Path

import requests
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from .api import Release
from .models import ReleaseStatus
from .utils import curator_experiments

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024

blueprint = Blueprint(
    "cernopendata_curate",
    __name__,
    template_folder="templates",
    static_folder="static",
)


def _detect_payload_type(items):
    """Return 'documents' if items look like docs, 'records' otherwise."""
    if not items:
        return "records"
    sample = items[0]
    if (
        isinstance(sample, dict)
        and ("slug" in sample or "body" in sample)
        and "recid" not in sample
        and "files" not in sample
    ):
        return "documents"
    return "records"


def _check_experiment(experiment):
    """Ensure that the experiment name is valid."""
    if not Release.validate_experiment(experiment):
        abort(404)
    if experiment not in curator_experiments()["curator_experiments"]:
        abort(403)


@blueprint.route("/releases/api/list/<experiment>", methods=["GET"])
@login_required
def list_releases(experiment=None):
    """Return list of releases."""
    _check_experiment(experiment)
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
                "status": r.status.value,
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
    _check_experiment(experiment)
    return render_template(
        "cernopendata_pages/releases.html", experiment=experiment.upper()
    )


@blueprint.route("/releases/<experiment>", methods=["POST"])
@login_required
def release_upload(experiment):
    """Upload a new release into the system."""
    _check_experiment(experiment)
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

    payload_type = _detect_payload_type(payload)
    if payload_type == "records":
        create_dict = {"records": payload}
    else:
        for doc in payload:
            doc.setdefault("_source_filename", release_name)
        create_dict = {"documents": payload}

    release = Release.create(
        experiment=experiment,
        current_user=current_user,
        name=release_name,
        **create_dict,
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


@blueprint.route("/releases/<experiment>/<int:release_id>", methods=["PUT"])
def update_release(experiment, release_id):
    """Updte the metadata of a release: name, link and description."""
    data = request.get_json()
    release = _get_release(experiment, release_id)

    updated = release.update_metadata(data)

    return jsonify(updated)


@blueprint.route("/releases/api/<experiment>/<int:release_id>")
def release_json(experiment, release_id):
    """Get the release in json."""
    release = _get_release(experiment, release_id)
    return Response(
        json.dumps({"records": release._metadata.records}, indent=2),
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=release-{release_id}.json"
        },
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

    data = request.get_json(silent=True)
    if not data["records"]:
        flash("No records provided", "error")
        abort(400, "No records provided")

    if not isinstance(data["records"], list):
        flash("Records must be a list", "error")
        abort(400, "Records must be a list")
    release = _get_release(experiment, release_id, lock=ReleaseStatus.EDITING)
    release.update_records(data["records"], current_user)

    flash("Records updated successfully.", "success")
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/stage",
    methods=["POST"],
)
@login_required
def stage_release(experiment, release_id):
    """Insert the objects defined in the release in the current system."""
    release = _get_release(
        experiment, release_id, status=ReleaseStatus.READY, lock=ReleaseStatus.STAGING
    )
    try:
        release.stage(current_user)
        flash("Release staged successfully.", "success")

    except Exception as e:
        flash(f" :( Error staging the release {e}", "error")

    return redirect(f"/releases/{experiment}/{release_id}")


def _get_release(experiment, release_id, lock=False, status=None):
    """Given an experiment and a relese number, return the release object."""
    _check_experiment(experiment)

    release = Release.get(experiment, release_id)

    if not release:
        abort(404)
    if status and not release.is_status(status):
        abort(409)
    if lock and not release.lock(ReleaseStatus(release.status), lock, current_user):
        abort(409)

    return release


@blueprint.route("/releases/<experiment>/<int:release_id>/rollback", methods=["POST"])
@login_required
def rollback(experiment, release_id):
    """Remove the records from the instance."""
    release = _get_release(experiment, release_id, status=ReleaseStatus.STAGED)

    release.rollback(current_user)

    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route("/releases/<experiment>/<int:release_id>/publish", methods=["POST"])
@login_required
def publish(experiment, release_id):
    """Publish the records: put them in the search, and remove the box saying that they were work in progress."""
    release = _get_release(experiment, release_id, status=ReleaseStatus.STAGED)

    release.publish(current_user)
    flash("Release published!")
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/add_documents",
    methods=["POST"],
)
@login_required
def add_documents(experiment, release_id):
    """Add documents to a release."""
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Missing request body")

    release = _get_release(experiment, release_id)
    source = data.get("source", "json")

    if source == "urls":
        urls = data.get("urls", [])
        if not urls:
            abort(400, "Missing URLs")
        json_docs = []
        for url in urls:
            clean_url = url.split("?")[0]
            if not clean_url.endswith(".json"):
                return jsonify({"error": f"URL must point to a .json file: {url}"}), 400
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
            except Exception as e:
                return jsonify({"error": f"Failed to fetch {url}: {e}"}), 400
            filename = clean_url.rsplit("/", 1)[-1]
            payload = resp.json()
            payload = payload if isinstance(payload, list) else [payload]
            for doc in payload:
                doc.setdefault("_source_filename", filename)
            json_docs.extend(payload)
        docs = json_docs
    else:
        docs = data.get("documents")
        if not docs or not isinstance(docs, list):
            abort(400, "Missing or invalid documents")

    for doc in docs:
        content = doc.get("body", {}).get("content", "")
        if isinstance(content, str) and content.endswith(".md"):
            return (
                jsonify(
                    {
                        "error": f"Document '{doc.get('slug', '?')}' has a filename pointer "
                        "in body.content. Inline the markdown text before uploading."
                    }
                ),
                400,
            )

    release.add_documents(docs, current_user)

    return jsonify(
        {"status": "ok", "num_docs": release._metadata.num_docs, "documents": docs}
    )


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/upload_image",
    methods=["POST"],
)
@login_required
def upload_image(experiment, release_id):
    """Upload one or more images attached to a parent document."""
    parent_slug = request.form.get("parent_slug")
    if not parent_slug:
        abort(400, "Missing parent_slug")

    files = [
        image for image in request.files.getlist("images") if image and image.filename
    ]
    if not files:
        abort(400, "No image files provided")

    release = _get_release(experiment, release_id)

    parent = next(
        (doc for doc in release.documents if doc.get("slug") == parent_slug),
        None,
    )
    if not parent:
        abort(400, f"No document with slug '{parent_slug}' in release")

    images_root = Path(current_app.config["CERNOPENDATA_IMAGES_PATH"]).resolve()
    target_dir = (images_root / parent_slug).resolve()
    try:
        target_dir.relative_to(images_root)
    except ValueError:
        abort(400, "Invalid parent_slug")
    target_dir.mkdir(parents=True, exist_ok=True)

    already_existing = {p.name for p in target_dir.iterdir()}

    images = []
    for file in files:
        filename = secure_filename(file.filename or "").lower()
        if not filename:
            abort(400, "Invalid filename")
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            return (
                jsonify({"error": f"Unsupported image extension: {extension}"}),
                400,
            )

        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > MAX_IMAGE_SIZE:
            return (
                jsonify(
                    {
                        "error": f"Image '{filename}' exceeds maximum size of "
                        f"{MAX_IMAGE_SIZE} bytes"
                    }
                ),
                400,
            )

        target_path = (target_dir / filename).resolve()
        try:
            target_path.relative_to(target_dir)
        except ValueError:
            abort(400, "Invalid filename")

        if filename in already_existing:
            return (
                jsonify(
                    {
                        "error": f"Image '{filename}' already exists for "
                        f"'{parent_slug}'. Rename the file and try again."
                    }
                ),
                409,
            )
        already_existing.add(filename)

        file.save(str(target_path))
        images.append(
            {
                "filename": filename,
                "parent_slug": parent_slug,
                "url": f"/static/upload/{parent_slug}/{filename}",
            }
        )

    return jsonify({"status": "ok", "images": images})


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/images",
    methods=["GET"],
)
@login_required
def list_images(experiment, release_id):
    """Return all uploaded images for a release, grouped by parent document slug."""
    release = _get_release(experiment, release_id)
    images_root = Path(current_app.config["CERNOPENDATA_IMAGES_PATH"]).resolve()

    images = []
    for doc in release.documents:
        slug = doc.get("slug")
        if not slug:
            continue
        doc_dir = (images_root / slug).resolve()
        try:
            doc_dir.relative_to(images_root)
        except ValueError:
            continue
        if not doc_dir.is_dir():
            continue
        for entry in sorted(doc_dir.iterdir()):
            if entry.is_file() and entry.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
                images.append(
                    {
                        "filename": entry.name,
                        "parent_slug": slug,
                        "url": f"/static/upload/{slug}/{entry.name}",
                    }
                )

    return jsonify({"status": "ok", "images": images})


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/images/<parent_slug>/<filename>",
    methods=["DELETE"],
)
@login_required
def delete_image(experiment, release_id, parent_slug, filename):
    """Delete a single uploaded image from a release."""
    release = _get_release(experiment, release_id)

    parent = next(
        (doc for doc in release.documents if doc.get("slug") == parent_slug),
        None,
    )
    if not parent:
        abort(404, f"No document with slug '{parent_slug}' in release")

    images_root = Path(current_app.config["CERNOPENDATA_IMAGES_PATH"]).resolve()
    slug_dir = (images_root / parent_slug).resolve()
    try:
        slug_dir.relative_to(images_root)
    except ValueError:
        abort(400, "Invalid parent_slug")

    safe_filename = secure_filename(filename)
    if not safe_filename:
        abort(400, "Invalid filename")
    target_path = (slug_dir / safe_filename).resolve()
    try:
        target_path.relative_to(slug_dir)
    except ValueError:
        abort(400, "Invalid filename")

    if not target_path.is_file():
        abort(404, "Image not found")

    target_path.unlink()
    if slug_dir.is_dir() and not any(slug_dir.iterdir()):
        slug_dir.rmdir()

    return jsonify({"status": "ok"})


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/images/<parent_slug>/<filename>",
    methods=["PUT"],
)
@login_required
def rename_image(experiment, release_id, parent_slug, filename):
    """Rename a single uploaded image."""
    data = request.get_json(silent=True) or {}
    new_filename = data.get("filename")
    if not new_filename:
        abort(400, "Missing filename")

    release = _get_release(experiment, release_id)

    parent = next(
        (doc for doc in release.documents if doc.get("slug") == parent_slug),
        None,
    )
    if not parent:
        abort(404, f"No document with slug '{parent_slug}' in release")

    images_root = Path(current_app.config["CERNOPENDATA_IMAGES_PATH"]).resolve()
    slug_dir = (images_root / parent_slug).resolve()
    try:
        slug_dir.relative_to(images_root)
    except ValueError:
        abort(400, "Invalid parent_slug")

    safe_old = secure_filename(filename).lower()
    safe_new = secure_filename(new_filename).lower()
    if not safe_old or not safe_new:
        abort(400, "Invalid filename")

    new_extension = Path(safe_new).suffix.lower()
    if new_extension not in ALLOWED_IMAGE_EXTENSIONS:
        return (
            jsonify({"error": f"Unsupported image extension: {new_extension}"}),
            400,
        )

    source_path = (slug_dir / safe_old).resolve()
    target_path = (slug_dir / safe_new).resolve()
    try:
        source_path.relative_to(slug_dir)
        target_path.relative_to(slug_dir)
    except ValueError:
        abort(400, "Invalid filename")

    if not source_path.is_file():
        abort(404, "Image not found")

    if target_path == source_path:
        return jsonify(
            {
                "status": "ok",
                "image": {
                    "filename": safe_new,
                    "parent_slug": parent_slug,
                    "url": f"/static/upload/{parent_slug}/{safe_new}",
                },
            }
        )

    if target_path.exists():
        return (
            jsonify(
                {
                    "error": f"An image named '{safe_new}' already exists. "
                    "Choose a different name."
                }
            ),
            409,
        )

    source_path.rename(target_path)

    return jsonify(
        {
            "status": "ok",
            "image": {
                "filename": safe_new,
                "parent_slug": parent_slug,
                "url": f"/static/upload/{parent_slug}/{safe_new}",
            },
        }
    )


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/documents/<slug>",
    methods=["PUT"],
)
@login_required
def update_document(experiment, release_id, slug):
    """Update a document in a release."""
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Missing request body")
    updated_doc = data.get("document")
    if not updated_doc:
        abort(400, "Missing document data")

    release = _get_release(experiment, release_id)
    try:
        release.update_document(slug, updated_doc, current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify({"status": "ok"})


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
        status=[ReleaseStatus.DRAFT, ReleaseStatus.READY],
        lock=ReleaseStatus.EDITING,
    )
    release.fix_checks(current_user)

    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/validations/<int:validation_id>/enable",
    methods=["POST"],
)
@login_required
def enable_validation(experiment, release_id, validation_id):
    """Enables a validation."""
    release = _get_release(
        experiment,
        release_id,
        status=[ReleaseStatus.DRAFT, ReleaseStatus.READY],
    )
    data = request.get_json() or {}
    enabled = data.get("enabled")

    release.enable_validation(validation_id, enabled, current_user)

    return {"success": True}, 200
    # return redirect(f"/releases/{experiment}/{release_id}")
