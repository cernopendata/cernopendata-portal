"""Validation process."""

import json

from flask import current_app
from jsonschema import Draft4Validator

from .base import Validation


class RucioSchema(Validation):

    name = "Rucio datasets"
    error_message = "There are some rucio datasets that have not been expanded"


    def validate(self, release):
        """Check if there are any entries with rucio_dataset and no files."""

        errors =[]
        for i, record in enumerate(release.records):
            if "rucio_dataset" in record['metadata'] and "files" not in record['metadata']:
                errors.append("The record {i} has a rucio rule and no files")
        return errors


    def get_files_from_rucio_dataset(self, dataset):
        did_client=DIDClient()
        result={}
        def _recurse(scope,name):
            try:
                files=list(did_client.list_files(scope,name))
                if files:
                    for f in files:
                        did=f"{f['scope']}:{f['name']}"
                        result[did]={"size":f.get("bytes"),"checksum":f.get("adler32") or f.get("md5")}
                    return
            except Exception:
                pass
            for child in did_client.list_content(scope,name):
                if child["type"]=="FILE":
                    did=f"{child['scope']}:{child['name']}"
                    result[did]={"size":child.get("bytes"),"checksum":child.get("adler32") or child.get("md5")}
                else:
                    _recurse(child["scope"],child["name"])
        scope,name=did.split(":",1)
        _recurse(scope,name)
        return result
    def fix(self, release):
        """Fix the entries that have rucio_dataset and no files"""

        for i, record in enumerate(release.records):
            if "rucio_dataset" in record['metadata'] and "files" not in record['metadata']:
                record.metadata['files_rucio'] = self.get_files_from_rucio_dataset(record.metadata['rucio_dataset'])
