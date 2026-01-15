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

import json
import logging
import os
import time
import uuid
from os.path import exists, isdir

import click
import pkg_resources
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.attributes import flag_modified

from cernopendata.api import FileIndexMetadata, MultiURIFileObject, RecordFilesWithIndex
from cernopendata.modules.records.minters.docid import cernopendata_docid_minter
from cernopendata.modules.records.minters.recid import cernopendata_recid_minter
from cernopendata.modules.records.minters.termid import cernopendata_termid_minter

MODE_OPTIONS = [
    "insert",
    "replace",
    "insert-or-replace",
    "insert-or-skip",
    "delete",
    "delete-or-skip",
]


def setup_cli_logger(verbose=False):
    """Sets up a dedicated logger for CLI commands."""
    logger = logging.getLogger("cli_logger")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger


option_verbose = click.option(
    "verbose", "-v", "--verbose", is_flag=True, help="Output verbose logging messages"
)


def get_jsons_from_dir(dir):
    """Get JSON files inside a dir."""
    res = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".json"):
                res.append(os.path.join(root, file))
    return res


def _handle_record_files(record, data, logger=None):
    """Handles record files."""
    # let's make a copy of files, since we might change it
    logger = logging.getLogger(__name__) if not logger else logger
    verbose = logger.getEffectiveLevel() == logging.DEBUG
    real_files = []
    if "files" not in data:
        if "distribution" in record and "availability" in record["distribution"]:
            record["availability"] = record["distribution"]["availability"]
        else:
            # If the record doesn't have any files, it should be online
            record["availability"] = "online"
        return
    data["_file_indices"] = []
    record["_file_indices"] = []
    if data["files"] and verbose:
        logger.info(f"  -> Detected {len(data['files'])} files")
    for file in data["files"]:
        assert "uri" in file
        assert "size" in file
        assert "checksum" in file
        f = FileInstance.create()
        filename = file.get("uri").split("/")[-1:][0]
        f.set_uri(file.get("uri"), file.get("size"), file.get("checksum"))
        if "type" in file and file["type"] == "index.json":
            # We don't need to store the index
            FileIndexMetadata.create(
                record,
                f,
                description=file.get("description", filename),
                logger=logger,
            )
            f.delete()
        elif "type" in file and file["type"] == "index.txt":
            # The txt indexes should be ignored. Just delete the file
            f.delete()
        else:
            if verbose:
                logger.info(f"  -> Detected direct file {file.get('uri')}")
            real_files.append(file)
            try:
                obj = MultiURIFileObject.create_version(record.bucket, filename, f.id)
                file_info = {
                    "bucket": str(obj.bucket_id),
                    "checksum": obj.file.checksum,
                    "key": obj.key,
                    "version_id": str(obj.version_id),
                    "availability": "online",
                }
                file.update(file_info)
            except Exception as e:
                logger.error(
                    f"  -> Recid {data.get('recid')} file {filename} could not be loaded due to {str(e)}."
                )
    record["files"] = real_files
    data["files"] = real_files
    if record.files:
        record.files.flush()
    if record.file_indices:
        record.file_indices.flush()
        data["_file_indices"] = record["_file_indices"]
    record.check_availability()


def create_record(data, skip_files, logger=None):
    """Creates a new record."""
    id = uuid.uuid4()
    cernopendata_recid_minter(id, data)
    record = RecordFilesWithIndex.create(data, id_=id, with_bucket=not skip_files)
    if not skip_files:
        _handle_record_files(record, data, logger)

    return record


def update_record(pid, data, skip_files, logger=None):
    """Updates the given record."""
    record = RecordFilesWithIndex.get_record(pid.object_uuid)
    if not skip_files:
        for o in ObjectVersion.get_by_bucket(record.bucket).all():
            o.remove()
            FileInstance.query.filter_by(id=o.file_id).delete()
        FileIndexMetadata.delete_by_record(record=record)
    # This is to ensure that fields that do not appear in the new data
    # are not just kept from the previous version
    for k in list(record.keys()):
        if k in ["_bucket", "pids"]:
            continue
        if skip_files and k in ["files", "_files", "file_indices", "_file_indices"]:
            continue
        del record[k]
    record.update(data)
    if not skip_files:
        _handle_record_files(record, data, logger)
        record.update(data)
        db.session.commit()
    return record


def delete_record(pid, pid_field, logger=None):
    """Deletes a record, including its pid and all the buckets and files."""
    try:
        record = RecordFilesWithIndex.get_record(pid.object_uuid)
        for o in ObjectVersion.get_by_bucket(record.bucket).all():
            o.remove()
            FileInstance.query.filter_by(id=o.file_id).delete()
        FileIndexMetadata.delete_by_record(record=record)
        record.delete()
    except NoResultFound:
        logger.error(
            "The record does not exist (even if the pid does!). Removing the pid"
        )

    pid = PersistentIdentifier.get(pid_field, str(pid.pid_value))
    db.session.delete(pid)
    pid2 = PersistentIdentifier.get("oai", f"oai:cernopendata.cern:{pid.pid_value}")
    db.session.delete(pid2)
    return None


def create_doc(data, skip_files, logger=None):
    """Creates a new doc record."""
    id = uuid.uuid4()
    cernopendata_docid_minter(id, data)
    record = Record.create(data, id_=id)
    return record


def update_doc_or_glossary(pid, data, skip_files, logger=None):
    """Updates the given doc/glossary record."""
    record = Record.get_record(pid.object_uuid)
    # This is to ensure that fields that do not appear in the new data
    # are not just maintained from the previous version
    for k in list(record.keys()):
        del record[k]
    record.update(data)
    return record


def delete_doc_or_glossary(pid, pid_field, logger=None):
    """Deletes a document or a glossary term."""
    record = Record.get_record(pid.object_uuid)
    record.delete()
    pid = PersistentIdentifier.get(pid_field, str(pid.pid_value))
    db.session.delete(pid)


def create_glossary_term(data, skip_files, logger=None):
    """Creates a new glossary term record."""
    id = uuid.uuid4()
    cernopendata_termid_minter(id, data)
    record = Record.create(data, id_=id)
    return record


@click.group(chain=True)
def fixtures():
    """Automate site bootstrap process and testing."""


def _get_list_of_fixture_files(files, type, logger):
    """Return the list of files that should be loaded."""
    data_dir = None
    if files:
        if not exists(files[0]):
            logger.error(f"The path {files[0]} does not exist")
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
    delete_function=delete_record,
    logger=None,
):
    logger = logging.getLogger(__name__) if not logger else logger
    if mode not in MODE_OPTIONS:
        logger.error(
            f"Error: mode '{mode}' not understood. Available options are '{MODE_OPTIONS}'"
        )
        return
    indexer = RecordIndexer()
    schema = current_app.extensions["invenio-jsonschemas"].path_to_url(schema_name)
    verbose = logger.getEffectiveLevel() == logging.DEBUG

    record_json = _get_list_of_fixture_files(files, entry_type, logger)

    i = 1
    total_files = len(record_json)
    statistics = {"inserted": 0, "updated": 0, "error": 0, "skipped": 0, "deleted": 0}
    for filename in record_json:
        logger.info(f"Loading records from {filename} ({i}/{total_files})...")
        i += 1
        with open(filename, "rb") as source:
            json_data = json.load(source)
            for data in json_data:
                pid = load_entry_data(data, filename)
                if not pid:
                    continue
                logger.info(f"==> Processing {entry_type} {pid}")
                if verbose:
                    logger.info(f"  -> Detected DOI {data.get('doi')}")
                data["$schema"] = schema
                try:
                    pid_object = PersistentIdentifier.get(pid_field, pid)
                    if mode == "insert":
                        logger.error(
                            f"==> {entry_type.capitalize()} {pid} exists already; cannot insert it."
                        )
                        statistics["error"] += 1
                        return statistics
                    if mode == "insert-or-skip":
                        logger.warning(
                            f"==> {entry_type.capitalize()} {pid} already exists... skipping"
                        )
                        statistics["skipped"] += 1
                        continue
                    if mode in ("delete", "delete-or-skip"):
                        record = delete_function(pid_object, pid_field)
                        action = "deleted"
                    else:
                        record = update_function(pid_object, data, skip_files, logger)
                        action = "updated"
                except PIDDoesNotExistError:
                    if mode in ("replace", "delete", "delete-or-skip"):
                        logger.error(
                            f"==> {entry_type.capitalize()} {pid} does not exist; cannot {mode} it."
                        )
                        statistics["error"] += 1
                        if mode == "delete-or-skip":
                            continue
                        return statistics
                    record = create_function(data, skip_files, logger)
                    action = "inserted"
                try:
                    if record:
                        record.commit()
                    db.session.commit()
                    statistics[action] += 1
                except Exception as e:
                    logger.error(f"==> There was an exception during the commit: {e}")
                    statistics["error"] += 1
                    return statistics
                logger.info(f"==> {entry_type.capitalize()} {pid} {action}")
                if record:
                    indexer.index(record)
                db.session.expunge_all()
    return statistics


def _log_statistics(statistics, type, start_time, logger):
    total_records = sum([value for value in statistics.values()])
    logger.info(
        f"Processed {total_records} {type} ({statistics['inserted']} created, {statistics['updated']} updated, "
        f"{statistics['error']} error, {statistics['skipped']} skipped, {statistics['deleted']} deleted))"
    )
    end_time = time.time()
    duration_seconds = end_time - start_time
    records_per_second = total_records / duration_seconds if duration_seconds > 0 else 0
    logger.info(
        f"Processing took {(duration_seconds / 60):.2f} minutes "
        f"({records_per_second:.2f} {type} per second)"
    )


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
@option_verbose
@with_appcontext
def records(skip_files, files, profile, mode, verbose):
    """Load all records."""
    start_time = time.time()
    logger = setup_cli_logger(verbose)
    if profile:
        import cProfile
        import pstats
        from io import StringIO

        pr = cProfile.Profile()
        pr.enable()

    def load_record_data(data, filename):
        if not data:
            logger.warning(
                f"IGNORING a possibly broken or corrupted record entry in file {filename} ..."
            )
            return False
        return data["recid"]

    result = _process_fixture_files(
        files,
        "record",
        "records/record-v1.0.0.json",
        skip_files=skip_files,
        mode=mode,
        load_entry_data=load_record_data,
        pid_field="recid",
        update_function=update_record,
        create_function=create_record,
        delete_function=delete_record,
        logger=logger,
    )

    if profile:
        pr.disable()
        s = StringIO()
        sortby = "cumulative"
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

    _log_statistics(result, "records", start_time, logger)


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
@option_verbose
def glossary(files, mode, verbose):
    """Load glossary term records."""
    start_time = time.time()
    logger = setup_cli_logger(verbose)

    def load_glossary_data(data, filename):
        return data["anchor"]

    result = _process_fixture_files(
        files,
        "terms",
        "records/glossary-term-v1.0.0.json",
        True,
        mode,
        load_glossary_data,
        "termid",
        update_function=update_doc_or_glossary,
        create_function=create_glossary_term,
        delete_function=delete_doc_or_glossary,
        logger=logger,
    )

    _log_statistics(result, "terms", start_time, logger)


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
@option_verbose
@with_appcontext
def docs(files, mode, verbose):
    """Load demo article records."""
    start_time = time.time()
    logger = setup_cli_logger(verbose)

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

    result = _process_fixture_files(
        files,
        entry_type="docs",
        schema_name="records/docs-v1.0.0.json",
        skip_files=True,
        mode=mode,
        load_entry_data=read_doc_content,
        pid_field="docid",
        update_function=update_doc_or_glossary,
        create_function=create_doc,
        delete_function=delete_doc_or_glossary,
        logger=logger,
    )

    _log_statistics(result, "docs", start_time, logger)


@fixtures.command()
@with_appcontext
def pids():
    """Fetch and register PIDs."""
    from invenio_db import db
    from invenio_oaiserver.fetchers import oaiid_fetcher
    from invenio_oaiserver.minters import oaiid_minter
    from invenio_pidstore.errors import PIDDoesNotExistError
    from invenio_pidstore.fetchers import recid_fetcher
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus
    from invenio_records.models import RecordMetadata

    logger = setup_cli_logger()
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
                logger.info(f"Found {found}.")
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
                logger.warning(f"Skipped: {record.id}")
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
                logger.info(f"Found {found}.")
            except PIDDoesNotExistError:
                pid = oaiid_minter(record.id, record.json)
                db.session.add(pid)

            flag_modified(record, "json")
            assert record.json["_oai"]["id"]
            db.session.add(record)
            db.session.commit()
            db.session.expunge_all()
