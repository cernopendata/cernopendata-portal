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
from invenio_records_files.api import FileObject, FilesIterator, Record


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

    def __len__(self):
        """Get number of file indices."""
        return len(self.file_indices)

    def __iter__(self):
        """Get iterator."""
        self._it = iter(self.file_indices)
        return self

    def __next__(self):
        """Get next file item."""
        entry = next(self._it)
        return self.file_indices[entry]

    def __getitem__(self, key):
        """Get a specific file."""
        obj = self.file_indices[key]
        return FileIndexMetadata.get(None, obj["files"][0]["bucket"])

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
        self.file_cls = FileObject

    @property
    def file_indices(self):
        """Here we keep the file indices."""
        return FileIndexIterator(self)


class FileIndexMetadata:
    """Class for the FileIndexMetadata."""

    def __init__(self):
        """Initialize an object."""
        self._number_files = 0
        self._size = 0
        self._files = []

    def __repr__(self):
        """Representation of the object."""
        return str(self.dumps())

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
        print(f"The file index contains {len(index_content)} entries.")
        for entry in index_content:
            entry_file = FileInstance.create()
            entry_file.set_uri(entry["uri"], entry["size"], entry["checksum"])
            o = ObjectVersion.create(
                rb._bucket,
                f"{index_file_name}_{rb._number_files}",
                _file_id=entry_file.id,
            )
            f = FileObject(o, entry)
            entry["file_id"] = str(entry_file.id)
            rb._number_files += 1
            if not rb._number_files % 1000:
                print(f"    {rb._number_files} done")
            rb._size += entry["size"]
            rb._files.append(f)
        record["_file_indices"].append(rb.dumps())
        rb._record = record
        return rb

    @classmethod
    def get(cls, record_id, bucket_id):
        """Get a file index, based on the bucket."""
        obj = cls()
        obj._index_file_name = (
            BucketTag.query.filter_by(key="index_name", bucket_id=str(bucket_id))
            .one()
            .value
        )
        bucket = Bucket.get(bucket_id)
        for o in ObjectVersion.get_by_bucket(bucket).all():
            f = FileObject(o, {})
            # Let's put also the uri
            f["uri"] = FileInstance.get(str(o.file_id)).uri
            f["filename"] = f["uri"].split("/")[-1]
            obj._files.append(f)
            obj._size += f.obj.file.size
            obj._number_files += 1
        return obj

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
        files = [o.dumps() for o in self._files]
        return {
            "key": self._index_file_name,
            "number_files": self._number_files,
            "size": self._size,
            "files": files,
        }

    def flush(self):
        """Flushing the information into the object."""
        return self.dumps()
