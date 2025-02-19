# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017-2025 CERN.
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

"""Cold Storage API."""
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
from invenio_records_files.models import RecordsBuckets


class FileObjectCold(FileObject):
    """Overwrite the fileobject to get multiple URI."""

    @classmethod
    def create(self, bucket, filename, file_id):
        """Create a cold file object."""
        return ObjectVersion.create(bucket, filename, file_id)

    def dumps(self):
        """This one has the information about the cold URI stored in a ObjectVersionTag."""
        info = super(FileObjectCold, self).dumps()
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
        """Describe the QoS of the file."""
        if "availability" not in self.data:
            avl = "ready"
            for t in self.obj.tags:
                if t.key == "hot_deleted":
                    avl = "needs request"
            self.data["availability"] = avl
        return self.data["availability"]
