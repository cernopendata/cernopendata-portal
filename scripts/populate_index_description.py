import json
import os
import uuid
from datetime import datetime
from os.path import basename, exists, isdir

import click
from invenio_db import db
from invenio_files_rest.models import (
    Bucket,
    BucketTag,
    FileInstance,
    ObjectVersion,
    ObjectVersionTag,
)
from invenio_indexer.api import RecordIndexer
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from cernopendata.api import RecordFilesWithIndex


def get_jsons_from_dir(dir):
    """Get JSON files inside a dir."""
    res = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".json"):
                res.append(os.path.join(root, file))
    return res


def find_bucket(pid_object, name):
    print(f"LOOKIGN FOR THE BUCKET OF {pid_object} and {name}")
    for bucket in BucketTag.query.filter_by(value=str(pid_object), key="record"):
        print("CHECKING ONE OPTION")
        q = BucketTag.query.filter_by(
            value=name, key="index_name", bucket_id=bucket.bucket_id
        )
        print(q.count())
        if q.count() == 1:
            return q.one()

    return None


indexer = RecordIndexer()
record_json = get_jsons_from_dir("/tmp/opendata.cern.ch/data/records/")

i = 1
total_files = len(record_json)

for filename in record_json:
    click.echo(f"Loading records from {filename} ({i}/{total_files})...")
    i += 1
    with open(filename, "rb") as source:
        j = 1
        json_data = json.load(source)
        #            print("Looking for file_indices")

        for record in json_data:
            print(record["recid"])
            pid_object = PersistentIdentifier.get("recid", record["recid"]).object_uuid
            update = False

            my_record = RecordFilesWithIndex.get_record(pid_object)
            # print(my_record)
            if (
                "license" in record
                and record["license"]["attribution"]
                != my_record["license"]["attribution"]
            ):
                update = True
                print("LICENSE CHANGE!!")
                my_record["license"]["attribution"] = record["license"]["attribution"]

            if "files" in record:
                for file in record["files"]:
                    #                    print(file)
                    if "type" in file and file["type"] == "index.json":
                        bucket = find_bucket(pid_object, basename(file["uri"]))
                        if not bucket:
                            print("ERROR FINDING THE BUCKET")
                            dasdas
                            continue
                        buc_desc = BucketTag.query.filter_by(
                            bucket_id=str(bucket.bucket_id), key="description"
                        )
                        if buc_desc.count() > 0:
                            print("The description exists")
                            continue

                        print("WE HAVE TO CREATE A TAG!!")
                        update = True
                        desc = file.get("description", basename(file["uri"]))
                        #                        print(f"The description is {desc}")
                        try:
                            BucketTag.create(bucket.bucket_id, "description", desc)
                        except IntegrityError as e:
                            if isinstance(
                                e.orig, UniqueViolation
                            ):  # Check if it's specifically a UniqueViolation
                                #     print("Duplicate key error:", e)
                                pass
                            else:
                                print("DIFFERENT ERROR")
            if update:
                # my_record.flush_indices()
                my_record.commit()
                try:
                    indexer.index(my_record)
                except:
                    print("THE INDEXING FAILED!!!")

    db.session.commit()
