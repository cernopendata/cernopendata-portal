# -*- coding: utf-8 -*-
"""API for manipulating file indices associated to a record."""

import json
import logging
from collections import OrderedDict

from invenio_files_rest.models import (
    Bucket,
    BucketTag,
    FileInstance,
    ObjectVersion,
    ObjectVersionTag,
)
from invenio_records_files.api import FileObject, FilesIterator

from cernopendata.cold_storage.api import ColdRecord, FileAvailability


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
        obj = FileIndexMetadata.get(self.record, key)
        if obj:
            return self.file_cls(obj, self.file_indices.get(obj.key, {}))
        raise KeyError(key)

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


class RecordFilesWithIndex(ColdRecord):
    """Class for a Record with File Indices."""

    def __init__(self, *args, **kwargs):
        """Initialize the record."""
        super(RecordFilesWithIndex, self).__init__(*args, **kwargs)
        self.file_cls = MultiURIFileObject

    @property
    def file_indices(self):
        """Here we keep the file indices."""
        return FileIndexIterator(self)

    def flush_indices(self):
        """Updates the _file_indices information based on what exists on the database."""
        self["_file_indices"] = []
        # First, let's get all the file indices that this record has
        for elem in BucketTag.query.filter_by(value=str(self.id), key="record").all():
            self["_file_indices"].append(
                FileIndexMetadata.get(None, str(elem.bucket)).dumps()
            )
        self.check_availability()


class FileIndexMetadata:
    """Class for the FileIndexMetadata."""

    def __init__(self):
        """Initialize an object."""
        self._avl = {}
        self._number_files = 0
        self._size = 0
        self._files = []
        self._description = ""
        self._bucket = ""

    def __repr__(self):
        """Representation of the object."""
        return str(self.dumps())

    @classmethod
    def create(cls, record, file_object, description="", logger=None):
        """Method to create a FileIndex."""
        rb = cls()
        rb.model = record.model
        logger = logging.getLogger(__name__) if not logger else logger
        verbose = logger.getEffectiveLevel() == logging.DEBUG
        # Let's read the file
        my_file = file_object.storage().open()
        index_content = json.load(my_file)
        my_file.close()
        if verbose:
            logger.info(
                f"  -> Detected index file with {len(index_content)} entries {file_object.uri}"
            )

        index_file_name = file_object.uri.split("/")[-1:][0]

        rb._index_file_name = index_file_name
        rb._bucket = Bucket.create()
        rb._description = description
        BucketTag.create(rb._bucket, "index_name", index_file_name)
        BucketTag.create(rb._bucket, "record", record.model.id)
        BucketTag.create(rb._bucket, "description", description)
        for entry in index_content:
            entry_file = FileInstance.create()
            entry_file.set_uri(entry["uri"], entry["size"], entry["checksum"])
            o = ObjectVersion.create(
                rb._bucket,
                f"{index_file_name}_{rb._number_files}",
                _file_id=entry_file.id,
            )
            f = MultiURIFileObject(o, entry)
            if f.availability not in rb._avl:
                rb._avl[f.availability] = 0
            rb._avl[f.availability] += 1
            entry["file_id"] = str(entry_file.id)
            rb._number_files += 1
            if not rb._number_files % 1000 and verbose:
                logger.info(f"       {rb._number_files} entries processed")
            rb._size += entry["size"]
            rb._files.append(f)
        record["_file_indices"].append(rb.dumps())
        if verbose:
            logger.info(
                f"  -> Processed index file with {len(index_content)} entries {file_object.uri}"
            )
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
        tag = BucketTag.query.filter_by(
            bucket_id=str(bucket_id), key="description"
        ).first()
        obj._description = tag.value if tag else obj._index_file_name
        obj._bucket = Bucket.get(bucket_id)
        for o in ObjectVersion.get_by_bucket(obj._bucket).all():
            f = MultiURIFileObject(o, {})
            # Let's put also the uri
            f["uri"] = FileInstance.get(str(o.file_id)).uri
            f["filename"] = f["uri"].split("/")[-1]
            obj._files.append(f)
            obj._size += f.obj.file.size
            obj._number_files += 1
            if f.availability not in obj._avl:
                obj._avl[f["availability"]] = 0
            obj._avl[f["availability"]] += 1
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
            "availability": self._avl,
            "key": self._index_file_name,
            "number_files": self._number_files,
            "size": self._size,
            "files": files,
            "description": self._description,
            "bucket": str(self._bucket),
        }

    def flush(self):
        """Flushing the information into the object."""
        return self.dumps()


class MultiURIFileObject(FileObject):
    """Overwrite the fileobject to offer multiple locations to store the file.

    The extra URI will be stored in ObjectVersionTags.

    Files will have an availability, depending on the locations that are available.
    For instance, if a file is only stored on tape, the availability will be `on demand`, since the file
    needs to be staged before users can access it. If the file is available, the availability will be `online`
    """

    @classmethod
    def create_version(self, bucket, filename, file_id):
        """Create a MultiURIFileObject."""
        return ObjectVersion.create(bucket, filename, file_id)

    def dumps(self):
        """This one has the information about the cold URI stored in a ObjectVersionTag."""
        info = super(MultiURIFileObject, self).dumps()
        info["tags"] = {}
        for tagName in ("uri_cold", "hot_deleted"):
            tag = ObjectVersionTag.get(str(self.obj.version_id), tagName)
            if tag:
                info["tags"][tagName] = tag.value
        if "availability" in self.data:
            del self.data["availability"]
        info["availability"] = self.availability
        if "uri" not in info:
            file = FileInstance.get(str(self.obj.file_id))
            info["uri"] = file.uri
        return info

    @property
    def availability(self):
        """Defines the availability of a file: online (disk) or on demand (tape)."""
        if "availability" not in self.data:
            if ObjectVersionTag.get(str(self.obj.version_id), "hot_deleted"):
                self.data["availability"] = FileAvailability.ONDEMAND.value
            else:
                self.data["availability"] = FileAvailability.ONLINE.value
        return self.data["availability"]
