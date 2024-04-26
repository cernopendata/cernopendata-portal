# -*- coding: utf-8 -*-
"""API for manipulating file indices associated to a record."""

import json
from collections import OrderedDict

from invenio_files_rest.models import (
    Bucket,
    BucketTag,
    FileInstance,
    ObjectVersion,
    ObjectVersionTag,
)
from invenio_records_files.api import FilesIterator, Record
from invenio_cold_storage.api import FileObjectCold


class FileIndexIterator(object):
    """Class to iterate over the files."""

    def __init__(self, record):
        """Initialize iterator."""
        self._it = None
        self.record = record
        self.model = record.model

        self.file_indices = OrderedDict(
            [(f["key"], f) for f in self.record.get("_file_indices", [])]
        )

    def flush(self):
        """Flush changes to record."""
        file_indices = self.dumps()
        if file_indices:
            self.record["_file_indices"] = file_indices

    def dumps(self):
        """Serialize file indices from a record.

        :returns: List of serialized file indices.
        """
        indices = []
        for obj in self.file_indices:
            indices.append(self.file_indices[obj])
        return indices


class RecordFilesWithIndex(Record):
    """Class for a Record with File Indices."""

    def __init__(self, *args, **kwargs):
        """Initialize the record."""
        super(RecordFilesWithIndex, self).__init__(*args, **kwargs)
        self.file_cls = FileObjectCold

    @property
    def file_indices(self):
        """Here we keep the file indices."""
        return FileIndexIterator(self)

    @classmethod
    def get_record(self, record):
        """Get a record and all the file indices from the database"""
        entry=super(RecordFilesWithIndex, self).get_record(record)
        entry["_file_indices"]=[]
        for tag in BucketTag.query.filter_by(key="record", value=str(record)).all():
            entry["_file_indices"].append(FileIndexMetadata.get(tag.bucket_id))
        return entry

class FileIndexMetadata:
    """Class for the FileIndexMetadata."""

    def __repr__(self):
        """Representation of the object."""
        return str(self.dumps())

    @classmethod
    def get(cls, bucket):
        """Get a file index from the bucket """
        rb = cls()
        rb._index_file_name = BucketTag.query.filter_by(key="index_name", bucket_id=bucket).one().value
        rb._files = []
        rb._size=0
        rb._number_files=0
        for ov in ObjectVersion.get_by_bucket(bucket).all():
            rb._size += ov.file.size
            rb._number_files+=1
            f = FileObjectCold(ov, {})
            rb._files.append(f)
        return rb.dumps()
    @classmethod
    def create(cls, record, file_object):
        """Method to create a FileIndex."""
        rb = cls()
        rb.model = record.model
        # Let's read the file
        my_file = file_object.storage().open()
        index_content = json.load(my_file)
        my_file.close()

        index_file_name = file_object.uri.split("/")[-1:][0]

        rb._index_file_name = index_file_name
        rb._bucket = Bucket.create()
        BucketTag.create(rb._bucket, "index_name", index_file_name)
        BucketTag.create(rb._bucket, "record", record.model.id)
        rb._number_files = 0
        rb._size = 0
        rb._files = []
        for entry in index_content:
            entry_file = FileInstance.create()
            entry_file.set_uri(entry["uri"], entry["size"], entry["checksum"])
            o = ObjectVersion.create(
                rb._bucket,
                f"{index_file_name}_{rb._number_files}",
                _file_id=entry_file.id,
            )
            f = FileObjectCold(o, entry)
            entry["file_id"] = str(entry_file.id)
            rb._number_files += 1
            rb._size += entry["size"]
            rb._files.append(f)
        record["_file_indices"].append(rb.dumps())
        rb._record = record
        return rb

    @classmethod
    def delete_by_record(cls, record):
        """Delete all the file indexes of a given record."""
        for buckettag in BucketTag.query.filter_by(key="record", value=str(record.id)):
            bucket = Bucket.get(buckettag.bucket_id)
            for o in ObjectVersion.get_by_bucket(bucket).all():
                o.remove()
                o.file.delete()
            bucket.remove()

    def dumps(self):
        """Dumping."""
        files = [ o.dumps() for o in self._files ]
        return  {
            "key": self._index_file_name,
            "number_files": self._number_files,
            "size": self._size,
            "files": files,
        }

    def flush(self):
        """Flushing the information into the object."""
        return self.dumps()
