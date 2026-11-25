# This script adds the missing `adler32:` prefix to the file checksums stored as a bare hex value
# Run the script via cernopendata shell /code/scripts/fix_bare_checksums.py

import re

from invenio_db import db
from invenio_files_rest.models import BucketTag, FileInstance, ObjectVersion
from invenio_indexer.api import RecordIndexer
from invenio_records_files.models import RecordsBuckets
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.attributes import flag_modified

from cernopendata.api import RecordFilesWithIndex
from cernopendata.modules.releases.models import ReleaseMetadata

ADLER32 = re.compile(r"^[0-9a-fA-F]{1,8}$")

print("Starting script...")

skipped = []


def canonical(checksum):
    """Prefix a bare adler32 checksum. Return None if the value is not adler32 hex."""
    if not ADLER32.match(checksum):
        return None
    return f"adler32:{checksum}"


def fix_files(files, location):
    """Prefix the bare checksums of a list of file entries, in place."""
    fixed = 0
    for file in files or []:
        checksum = file.get("checksum")
        if isinstance(checksum, str) and ":" not in checksum:
            prefixed = canonical(checksum)
            if prefixed:
                file["checksum"] = prefixed
                fixed += 1
            else:
                skipped.append(f"{location}, {file.get('uri')}: {checksum}")
    return fixed


bare_files = FileInstance.query.filter(FileInstance.checksum.notlike("%:%")).all()
bare_file_ids = [instance.id for instance in bare_files]

print("Fixing the checksums copied into the record metadata...")
indexer = RecordIndexer()
bucket_ids = {
    bucket_id
    for (bucket_id,) in db.session.query(ObjectVersion.bucket_id).filter(
        ObjectVersion.file_id.in_(bare_file_ids)
    )
}
records_owning_the_files = db.session.query(RecordsBuckets.record_id).filter(
    RecordsBuckets.bucket_id.in_(bucket_ids)
)
records_indexing_the_files = db.session.query(cast(BucketTag.value, UUID)).filter(
    BucketTag.key == "record", BucketTag.bucket_id.in_(bucket_ids)
)
for (record_id,) in records_owning_the_files.union(records_indexing_the_files):
    record = RecordFilesWithIndex.get_record(record_id)
    location = f"recid {record.get('recid')}"
    fixed = fix_files(record.get("files"), location)
    fixed += fix_files(record.get("_files"), location)
    for index in record.get("_file_indices", []):
        fixed += fix_files(index.get("files"), location)
    if not fixed:
        continue
    print(f" - {location}: {fixed} checksums")
    record.commit()
    db.session.commit()
    indexer.index(record)

print("Fixing the file checksums, used to serve the downloads...")
for instance in bare_files:
    checksum = canonical(instance.checksum)
    if checksum:
        instance.checksum = checksum
        print(f" - {instance.uri}")
    else:
        skipped.append(f"file instance {instance.uri}: {instance.checksum}")
db.session.commit()

print("Fixing the checksums stored in the releases...")
for release in ReleaseMetadata.query.order_by(ReleaseMetadata.id):
    fixed = 0
    location = f"release {release.id} ({release.name})"
    for record in release.records or []:
        fixed += fix_files(record.get("files"), location)
    if not fixed:
        continue
    print(f" - {location}: {fixed} checksums")
    flag_modified(release, "records")
    db.session.add(release)
db.session.commit()

print("Script completed")
if skipped:
    print(f" - {len(skipped)} checksums are not adler32 hex and were left untouched:")
    for entry in skipped:
        print(f"     {entry}")
