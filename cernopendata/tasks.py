# -*- coding: utf-8 -*-
"""Celery tasks used by the CERN Open Data portal."""

import hashlib
import json
import logging
from datetime import datetime

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_files_rest.models import BucketTag, FileInstance, ObjectVersion
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from invenio_search.engine import search
from invenio_search.proxies import current_search_client
from sqlalchemy import cast, or_
from sqlalchemy.dialects.postgresql import UUID

logger = logging.getLogger(__name__)


EOS_DUMP_PATH = "/eos/workspace/c/cernod/dumps/opendata/latest"
IGNORED_PATH = "/upload/"
PREFIX = "root://eospublic.cern.ch/"
BATCH_SIZE = 1000

ProcessEosDumpTask = {"task": "cernopendata.tasks.process_eos_dump"}


@shared_task
def process_eos_dump():
    """Process the latest EOS dump."""
    logging.info("Starting processing EOS dump...")
    current_batch = []
    batch_count = 0
    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for entry in _stream_dump_file(EOS_DUMP_PATH):
        path = entry["path"]

        if IGNORED_PATH in path:
            skipped_count += 1
            continue

        current_batch.append(entry)

        if len(current_batch) >= BATCH_SIZE:
            batch_count += 1
            try:
                _process_batch(current_batch)
                processed_count += len(current_batch)
            except Exception as e:
                logger.error(f"Failed to process batch {batch_count}: {str(e)}")
                failed_count += len(current_batch)
            current_batch = []

    if current_batch:
        batch_count += 1
        logging.info(f"- Processing batch {batch_count} of size {len(current_batch)}")
        try:
            _process_batch(current_batch)
        except Exception as e:
            logger.error(f"Failed to process batch {batch_count}: {str(e)}")

    logging.info(
        f"Finished processing: Processed {processed_count} entries. "
        f"Skipped {skipped_count} entries. "
        f"Failed to process {failed_count} entries."
    )


def _stream_dump_file(filepath):
    with open(filepath, "r") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _process_batch(dump_entries):
    index_prefix = current_app.config.get("SEARCH_INDEX_PREFIX")
    mapping_index = f"{index_prefix}records-recid_mapping"
    dark_index = f"{index_prefix}dark-files"

    needs_db_check = []
    actions = []

    # Compare dump entries with mapping index
    existing_mapping_info = _get_existing_mapping_info(dump_entries, mapping_index)
    existing_entries_to_update = []
    for entry in dump_entries:
        path = entry.get("path")
        if path in existing_mapping_info:
            dump_last_accessed = datetime.fromtimestamp(entry["atime"]).isoformat()
            if existing_mapping_info[path]["last_accessed"] != dump_last_accessed:
                existing_entries_to_update.append(entry)
        else:
            # If entry is not found in the index, check database
            needs_db_check.append(entry)

    # Update last_accessed for existing entries in one update_by_query operation
    if existing_entries_to_update:
        _update_last_accessed(existing_entries_to_update, mapping_index)

    if not needs_db_check:
        return

    # Query database for dump entries not found in the index
    dump_mapping = {
        _normalize_dump_path(entry["path"]): entry for entry in needs_db_check
    }
    records = _get_records_by_paths(dump_mapping.keys())
    db_mapping = {record[0]: record[1] for record in records}

    existing_dark_info = _get_existing_mapping_info(needs_db_check, dark_index)
    dark_entries_to_update = []
    for full_uri, dump_entry in dump_mapping.items():
        path = dump_entry.get("path")
        if full_uri in db_mapping:
            # If file path found in database, add it to the mapping index
            record = _transform_from_db(dump_entry, db_mapping[full_uri])
            actions.append(
                {
                    "_index": mapping_index,
                    "_id": _path_to_id(path),
                    "_source": record,
                }
            )

            # If file path found in the database and in the dark files index, remove it from the index
            if path in existing_dark_info:
                actions.append(
                    {
                        "_op_type": "delete",
                        "_index": dark_index,
                        "_id": existing_dark_info[path]["id"],
                    }
                )
        elif path in existing_dark_info:
            # If already in dark index, update last_accessed if it has changed
            dump_last_accessed = datetime.fromtimestamp(dump_entry["atime"]).isoformat()
            if existing_dark_info[path]["last_accessed"] != dump_last_accessed:
                dark_entries_to_update.append(dump_entry)
        else:
            # If not in database and not in dark index, add it
            record = _transform_dark_file(dump_entry)
            actions.append(
                {"_index": dark_index, "_id": _path_to_id(path), "_source": record}
            )

    if dark_entries_to_update:
        _update_last_accessed(dark_entries_to_update, dark_index)

    if actions:
        # Index bulk update
        success, errors = search.helpers.bulk(
            current_search_client, actions, stats_only=True
        )
        if errors:
            logger.error(f"Failed to index {errors} items.")
        else:
            logger.info(f"Processed {success} items across indexes.")

    db.session.expunge_all()


def _update_last_accessed(entries, index):
    last_accessed_mapping = {
        entry["path"]: datetime.fromtimestamp(entry["atime"]).isoformat()
        for entry in entries
    }
    body = {
        "query": {"terms": {"uri": list(last_accessed_mapping.keys())}},
        "script": {
            "lang": "painless",
            "source": "ctx._source.last_accessed = params.last_accessed_mapping[ctx._source.uri]",
            "params": {"last_accessed_mapping": last_accessed_mapping},
        },
    }
    result = current_search_client.update_by_query(
        index=index, body=body, conflicts="proceed"
    )
    if result.get("failures"):
        logger.error(f"Failed to update {result['failures']} items.")
    else:
        logger.info(f"Successfully updated {result.get('updated', 0)} items.")


def _get_existing_mapping_info(entries, index):
    if not entries:
        return {}
    paths = [entry["path"] for entry in entries]
    query = {"query": {"terms": {"uri": paths}}, "_source": ["uri", "last_accessed"]}
    try:
        result = current_search_client.search(index=index, body=query, size=len(paths))
    except search.exceptions.NotFoundError:
        return {}
    return {
        hit["_source"]["uri"]: {
            "id": hit["_id"],
            "last_accessed": hit["_source"].get("last_accessed"),
        }
        for hit in result["hits"]["hits"]
    }


def _path_to_id(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _get_records_by_paths(paths):
    rows = (
        db.session.query(
            FileInstance.uri,
            RecordMetadata.json["title"].as_string().label("title"),
            RecordMetadata.json["recid"].as_string().label("recid"),
            RecordMetadata.json["date_published"].as_string().label("date_published"),
        )
        .join(ObjectVersion, ObjectVersion.file_id == FileInstance.id)
        .outerjoin(RecordsBuckets, RecordsBuckets.bucket_id == ObjectVersion.bucket_id)
        .outerjoin(
            BucketTag,
            (BucketTag.bucket_id == ObjectVersion.bucket_id)
            & (BucketTag.key == "record"),
        )
        .join(
            RecordMetadata,
            or_(
                RecordMetadata.id == RecordsBuckets.record_id,
                RecordMetadata.id == cast(BucketTag.value, UUID),
            ),
        )
        .filter(FileInstance.uri.in_(paths))
        .all()
    )
    return [
        (
            row.uri,
            {
                "title": row.title,
                "recid": row.recid,
                "date_published": row.date_published,
            },
        )
        for row in rows
    ]


def _transform_from_db(dump_entry, record_data):
    return {
        "uri": dump_entry["path"],
        "timestamp": datetime.utcnow().isoformat(),
        "title": record_data.get("title"),
        "recid": record_data.get("recid"),
        "year_published": record_data.get("date_published"),
        "last_accessed": datetime.fromtimestamp(dump_entry["atime"]).isoformat(),
    }


def _transform_dark_file(dump_entry):
    return {
        "uri": dump_entry["path"],
        "size": dump_entry["size"],
        "adler32": dump_entry.get("adler32"),
        "last_modified": datetime.fromtimestamp(dump_entry["mtime"]).isoformat(),
        "last_accessed": datetime.fromtimestamp(dump_entry["atime"]).isoformat(),
    }


def _normalize_dump_path(dump_path):
    return f"{PREFIX}{dump_path}"
