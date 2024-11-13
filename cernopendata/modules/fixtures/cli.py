# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017, 2018, 2020,2022 CERN.
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

"""Command line interface for CERN Open Data Portal."""

import glob
import json
import os
import uuid
from datetime import datetime
from os.path import exists, isdir

import click
import pkg_resources
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import (
    Bucket,
    BucketTag,
    FileInstance,
    ObjectVersion,
    ObjectVersionTag,
)
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from sqlalchemy.orm.attributes import flag_modified

from cernopendata.api import FileIndexMetadata, RecordFilesWithIndex
from cernopendata.modules.records.minters.docid import cernopendata_docid_minter
from cernopendata.modules.records.minters.recid import cernopendata_recid_minter
from cernopendata.modules.records.minters.termid import cernopendata_termid_minter

MODE_OPTIONS = ["insert", "replace", "insert-or-replace", "insert-or-skip"]


def get_jsons_from_dir(dir):
    """Get JSON files inside a dir."""
    res = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".json"):
                res.append(os.path.join(root, file))
    return res


def _handle_record_files(record, data):
    """Handles record files."""
    # let's make a copy of files, since we might change it
    real_files = []
    if "files" not in data:
        return
    data["_file_indices"] = []
    record["_file_indices"] = []
    for file in data["files"]:
        assert "uri" in file
        assert "size" in file
        assert "checksum" in file
        f = FileInstance.create()
        filename = file.get("uri").split("/")[-1:][0]
        f.set_uri(file.get("uri"), file.get("size"), file.get("checksum"))
        if "type" in file and file["type"] == "index.json":
            print(
                datetime.now(),
                "This is an index file. Let's check the entries that it has:",
                file.get("uri"),
            )
            # We don't need to store the index
            FileIndexMetadata.create(record, f)
            print("File index created")
            f.delete()
        elif "type" in file and file["type"] == "index.txt":
            # The txt indexes should be ignored. Just delete the file
            f.delete()
        else:
            real_files.append(file)
            try:
                obj = ObjectVersion.create(record.bucket, filename, _file_id=f.id)
                file_info = {
                    "bucket": str(obj.bucket_id),
                    "checksum": obj.file.checksum,
                    "key": obj.key,
                    "version_id": str(obj.version_id),
                }
                file.update(file_info)
            except Exception as e:
                click.secho(
                    "Recid {0} file {1} could not be loaded due "
                    "to {2}.".format(data.get("recid"), filename, str(e)),
                    fg="red",
                    err=True,
                )
    record["files"] = real_files
    data["files"] = real_files
    if record.files:
        record.files.flush()
    if record.file_indices:
        record.file_indices.flush()
        data["_file_indices"] = record["_file_indices"]


def create_record(data, skip_files):
    """Creates a new record."""
    id = uuid.uuid4()
    cernopendata_recid_minter(id, data)
    record = RecordFilesWithIndex.create(data, id_=id, with_bucket=not skip_files)
    if not skip_files:
        _handle_record_files(record, data)

    return record


def update_record(pid, data, skip_files):
    """Updates the given record."""
    record = RecordFilesWithIndex.get_record(pid.object_uuid)
    if not skip_files:
        for o in ObjectVersion.get_by_bucket(record.bucket).all():
            o.remove()
            FileInstance.query.filter_by(id=o.file_id).delete()
        FileIndexMetadata.delete_by_record(record=record)
    # This is to ensure that fields that do not appear in the new data
    # are not just maintained from the previous version
    for k in list(record.keys()):
        if skip_files and k in ["files", "_files", "file_indices", "_file_indices"]:
            continue
        del record[k]
    record.update(data)
    if not skip_files:
        _handle_record_files(record, data)
        record.update(data)
        db.session.commit()
    return record


def create_doc(data, skip_files):
    """Creates a new doc record."""
    id = uuid.uuid4()
    cernopendata_docid_minter(id, data)
    record = Record.create(data, id_=id)
    return record


def update_doc_or_glossary(pid, data, skip_files):
    """Updates the given doc/glossary record."""
    record = Record.get_record(pid.object_uuid)
    # This is to ensure that fields that do not appear in the new data
    # are not just maintained from the previous version
    for k in list(record.keys()):
        del record[k]
    record.update(data)
    return record


def create_glossary_term(data, skip_files):
    """Creates a new glossary term record."""
    id = uuid.uuid4()
    cernopendata_termid_minter(id, data)
    record = Record.create(data, id_=id)
    return record


@click.group(chain=True)
def fixtures():
    """Automate site bootstrap process and testing."""


def _get_list_of_fixture_files(files, type):
    """Return the list of files that should be loaded."""
    data_dir = None
    if files:
        if not exists(files[0]):
            click.secho(
                f"The path {files[0]} does not exist",
                fg="red",
                err=True,
            )
            return
        if isdir(files[0]):
            data_dir = files[0]
        else:
            return files
    if not data_dir:
        data_dir = pkg_resources.resource_filename(
            "cernopendata", f"modules/fixtures/data/{type}"
        )

    return get_jsons_from_dir(data_dir)


def _process_fixture_files(
    files,
    entry_type,
    schema_name,
    skip_files,
    mode,
    load_entry_data,
    pid_field,
    update_function=update_record,
    create_function=create_record,
):
    if mode not in MODE_OPTIONS:
        click.secho(
            f"Error: mode '{mode}' not understood. Available options are '{MODE_OPTIONS}'",
            fg="red",
            err=True,
        )
        return
    indexer = RecordIndexer()
    schema = current_app.extensions["invenio-jsonschemas"].path_to_url(schema_name)

    record_json = _get_list_of_fixture_files(files, entry_type)

    i = 1
    total_files = len(record_json)
    for filename in record_json:
        click.echo(f"Loading records from {filename} ({i}/{total_files})...")
        i += 1
        with open(filename, "rb") as source:
            j = 1
            json_data = json.load(source)
            records_file = len(json_data)
            for data in json_data:
                pid = load_entry_data(data, filename)
                if not pid:
                    continue
                data["$schema"] = schema
                try:
                    pid_object = PersistentIdentifier.get(pid_field, pid)
                    if mode == "insert":
                        click.secho(
                            f"{entry_type} {pid} exists already; cannot insert it.",
                            fg="red",
                            err=True,
                        )
                        return
                    if mode == "insert-or-skip":
                        click.secho(f"{entry_type} {pid} already exists... skipping")
                        continue
                    record = update_function(pid_object, data, skip_files)
                    action = "updated"
                except PIDDoesNotExistError:
                    if mode == "replace":
                        click.secho(
                            f"{entry_type} {pid} does not exist; cannot replace it.",
                            fg="red",
                            err=True,
                        )
                        return
                    record = create_function(data, skip_files)
                    action = "inserted"
                try:
                    record.commit()
                    db.session.commit()
                except Exception as e:
                    click.secho(
                        f"There was an exception during the commit: {e}",
                        fg="red",
                        err=True,
                    )
                    return
                click.echo(f"{entry_type} {pid} {action}")
                indexer.index(record)
                db.session.expunge_all()


@fixtures.command()
@click.option("--skip-files", is_flag=True, default=False, help="Skip loading of files")
@click.option(
    "files",
    "--file",
    "-f",
    multiple=True,
    type=click.Path(exists=True),
    help="Path to the file(s) to be loaded. If not provided, all"
    "files will be loaded",
)
@click.option("--profile", is_flag=True, help="Output profiling information.")
@click.option(
    "--mode",
    required=True,
    type=click.Choice(MODE_OPTIONS),
    default="insert-or-replace",
)
@with_appcontext
def records(skip_files, files, profile, mode):
    """Load all records."""
    if profile:
        import cProfile
        import pstats
        from io import StringIO

        pr = cProfile.Profile()
        pr.enable()

    def load_record_data(data, filename):
        if not data:
            click.echo(
                "IGNORING a possibly broken or corrupted "
                "record entry in file {0} ...".format(filename)
            )
            return False
        return data["recid"]

    _process_fixture_files(
        files,
        "record",
        "records/record-v1.0.0.json",
        skip_files=skip_files,
        mode=mode,
        load_entry_data=load_record_data,
        pid_field="recid",
        update_function=update_record,
        create_function=create_record,
    )

    if profile:
        pr.disable()
        s = StringIO()
        sortby = "cumulative"
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())


@fixtures.command()
@with_appcontext
@click.option(
    "files",
    "--file",
    "-f",
    multiple=True,
    type=click.Path(exists=True),
    help="Path to the file(s) to be loaded. If not provided, all"
    "files will be loaded",
)
@click.option(
    "--mode",
    required=True,
    type=click.Choice(MODE_OPTIONS),
    default="insert-or-replace",
)
def glossary(files, mode):
    """Load glossary term records."""

    def load_glossary_data(data, filename):
        return data["anchor"]

    _process_fixture_files(
        files,
        "terms",
        "records/glossary-term-v1.0.0.json",
        True,
        mode,
        load_glossary_data,
        "termid",
        update_doc_or_glossary,
        create_glossary_term,
    )


@fixtures.command()
@click.option(
    "files",
    "--file",
    "-f",
    multiple=True,
    type=click.Path(exists=True),
    help="Path to the file(s) to be loaded. If not provided, all"
    "files will be loaded",
)
@click.option(
    "--mode",
    required=True,
    type=click.Choice(MODE_OPTIONS),
    default="insert-or-replace",
)
@with_appcontext
def docs(files, mode):
    """Load demo article records."""

    def read_doc_content(data, filename):
        assert data["body"]["content"]
        assert data["slug"]
        content_filename = os.path.join(
            *(
                [
                    "/",
                ]
                + filename.split("/")[:-1]
                + [
                    data["body"]["content"],
                ]
            )
        )

        with open(content_filename) as body_field:
            data["body"]["content"] = body_field.read()
        return data["slug"]

    _process_fixture_files(
        files,
        entry_type="docs",
        schema_name="records/docs-v1.0.0.json",
        skip_files=True,
        mode=mode,
        load_entry_data=read_doc_content,
        pid_field="docid",
        update_function=update_doc_or_glossary,
        create_function=create_doc,
    )


@fixtures.command()
@with_appcontext
def pids():
    """Fetch and register PIDs."""
    from invenio_db import db
    from invenio_oaiserver.fetchers import onaiid_fetcher
    from invenio_oaiserver.minters import oaiid_minter
    from invenio_pidstore.errors import PIDDoesNotExistError
    from invenio_pidstore.fetchers import recid_fetcher
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus
    from invenio_records.models import RecordMetadata

    recids = [r.id for r in RecordMetadata.query.all()]
    db.session.expunge_all()

    with click.progressbar(recids) as bar:
        for record_id in bar:
            record = RecordMetadata.query.get(record_id)
            try:
                pid = recid_fetcher(record.id, record.json)
                found = PersistentIdentifier.get(
                    pid_type=pid.pid_type,
                    pid_value=pid.pid_value,
                    pid_provider=pid.provider.pid_provider,
                )
                click.echo("Found {0}.".format(found))
            except PIDDoesNotExistError:
                db.session.add(
                    PersistentIdentifier.create(
                        pid.pid_type,
                        pid.pid_value,
                        object_type="rec",
                        object_uuid=record.id,
                        status=PIDStatus.REGISTERED,
                    )
                )
            except KeyError:
                click.echo("Skiped: {0}".format(record.id))
                continue

            pid_value = record.json.get("_oai", {}).get("id")
            if pid_value is None:
                pid_value = current_app.config.get("OAISERVER_ID_PREFIX") + str(
                    record.json["recid"]
                )

                record.json.setdefault("_oai", {})
                record.json["_oai"]["id"] = pid.pid_value

            pid = oaiid_fetcher(record.id, record.json)
            try:
                found = PersistentIdentifier.get(
                    pid_type=pid.pid_type,
                    pid_value=pid.pid_value,
                    pid_provider=pid.provider.pid_provider,
                )
                click.echo("Found {0}.".format(found))
            except PIDDoesNotExistError:
                pid = oaiid_minter(record.id, record.json)
                db.session.add(pid)

            flag_modified(record, "json")
            assert record.json["_oai"]["id"]
            db.session.add(record)
            db.session.commit()
            db.session.expunge_all()
