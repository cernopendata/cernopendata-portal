import json

import requests
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
)
from flask_login import current_user, login_required
from invenio_db import db
from werkzeug.exceptions import BadRequest

from .models import Release


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

    releases = (
        db.session.query(Release)
        .filter(Release.experiment == experiment)
        .order_by(Release.created_at.desc())
        .all()
    )

    # Serialize
    def serialize_user(user):
        if not user:
            return None
        return {
            "id": user.id,
            "email": user.email,
        }

    return jsonify(
        [
            {
                "id": r.id,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "created_by": serialize_user(r.created_by),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "updated_by": serialize_user(r.updated_by),
                "released_at": r.released_at.isoformat() if r.released_at else None,
                "num_records": r.num_records,
                "num_docs": r.num_docs,
                "num_glossaries": r.num_glossaries,
                "valid_recid": r.valid_recid,
                "valid_doi": r.valid_doi,
                "num_errors": r.num_errors,
                "num_files": r.num_files,
                "valid_files": r.valid_files,
            }
            for r in releases
        ]
    )


@blueprint.route("/releases/<experiment>")
@login_required
def release_view(experiment=None):
    """Landing page for the curation process"""
    if not Release.validate_experiment(experiment):
        abort(404)

    if experiment != "atlas":  # not curate_permission(experiment).can():
        abort(403)
    return render_template(
        "cernopendata_pages/releases.html", experiment=experiment.upper()
    )


@blueprint.route("/releases/<experiment>", methods=["POST"])
@login_required
def release_upload(experiment):
    if not Release.validate_experiment(experiment):
        abort(404)

    if experiment != "atlas":  # not curate_permission(experiment).can():
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

    elif source == "url":
        url = request.form.get("url")
        if not url:
            abort(400, "Missing URL")

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()

    else:
        abort(400, "Invalid source")

    release = Release.create(
        records=payload,
        experiment=experiment,
        created_by=current_user,
    )

    flash(f"Release {release.id} created.", "success")

    return render_template(
        "cernopendata_pages/releases.html", experiment=experiment.upper()
    )


@blueprint.route("/releases/<experiment>/<int:release_id>")
def release_detail(experiment, release_id):
    release = _get_release(experiment, release_id)

    return render_template(
        "cernopendata_pages/release_details.html",
        release=release,
        experiment=experiment,
    )


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/generate_recid",
    methods=["POST"],
)
def generate_recid(experiment, release_id):
    release = _get_release(
        experiment, release_id, lock=True, status=Release.STATUS_DRAFT
    )

    release.generate_recids()
    release.validate()
    db.session.add(release)
    db.session.commit()

    flash(f"Recid created for records in release {release.id}.", "success")

    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/generate_doi",
    methods=["POST"],
)
def generate_doi(experiment, release_id):
    release = _get_release(
        experiment, release_id, lock=True, status=Release.STATUS_DRAFT
    )

    if release.valid_doi:
        abort(400, "RECIDs already generated")

    release.generate_doi()
    db.session.add(release)
    release.validate()
    db.session.commit()

    flash(f"Recid created for records in release {release.id}.", "success")

    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/delete",
    methods=["POST"],
)
@login_required
def delete_release(experiment, release_id):
    release = _get_release(experiment, release_id)

    db.session.delete(release)
    db.session.commit()

    flash("Release deleted successfully.", "success")

    return redirect(f"/releases/{experiment}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/update_records",
    methods=["POST"],
)
@login_required
def update_records(experiment, release_id):
    release = _get_release(experiment, release_id, lock=True)

    # Get JSON string from form
    records_json = request.form.get("records_json")
    if not records_json:
        abort(400, "No records provided")

    try:
        release.records = json.loads(records_json)
        if not isinstance(release.records, list):
            raise ValueError("Records must be a list")
    except ValueError as e:
        abort(400, f"Invalid JSON: {e}")

    release.validate(current_user)
    db.session.add(release)
    db.session.commit()

    flash("Records updated successfully.", "success")
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/deploy",
    methods=["POST"],
)
@login_required
def deploy_release(experiment, release_id):
    release = _get_release(experiment, release_id, status=Release.STATUS_READY)
    schema = "local://records/record-v1.0.0.json"
    try:
        release.deploy(schema)
        db.session.add(release)
        db.session.commit()
        flash("Release deployed successfully.", "success")

    except Exception as e:
        flash(f" :( Error deploying the release {e}", "error")

    return redirect(f"/releases/{experiment}/{release_id}")


def _get_release(experiment, release_id, lock=False, status=None):
    if not Release.validate_experiment(experiment):
        abort(404)

    if experiment != "atlas":  # not curate_permission(experiment).can():
        abort(403)

    release = Release.query.filter_by(
        id=release_id, experiment=experiment
    ).first_or_404()

    if lock and not release.lock_for_editing():
        abort(409)

    if status and release.status != status:
        abort(409)

    return release


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/generate_file_metadata",
    methods=["POST"],
)
@login_required
def generate_filemetadata(experiment, release_id):
    release = _get_release(
        experiment, release_id, lock=True, status=Release.STATUS_DRAFT
    )

    if release.generate_filemetadata():
        db.session.add(release)
        flash("Release updated.", "success")
    else:
        flash("No file was updated. Could it be that there are no files?", "warning")
    release.validate()
    db.session.commit()
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route("/releases/<experiment>/<int:release_id>/rollback", methods=["POST"])
@login_required
def rollback(experiment, release_id):
    release = _get_release(experiment, release_id, status=Release.STATUS_DEPLOYED)

    release.rollback()
    db.session.commit()

    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route("/releases/<experiment>/<int:release_id>/publish", methods=["POST"])
@login_required
def publish(experiment, release_id):
    release = _get_release(experiment, release_id, status=Release.STATUS_DEPLOYED)

    schema = "local://records/record-v1.0.0.json"

    release.publish(schema)
    db.session.commit()
    flash("Release published!")
    return redirect(f"/releases/{experiment}/{release_id}")


@blueprint.route(
    "/releases/<experiment>/<int:release_id>/expand_files", methods=["POST"]
)
@login_required
def expand_files(experiment, release_id):
    release = _get_release(
        experiment, release_id, lock=True, status=Release.STATUS_DRAFT
    )

    release.expand_files()
    release.validate()
    db.session.commit()
    flash("Release updated.", "success")
    return redirect(f"/releases/{experiment}/{release_id}")
