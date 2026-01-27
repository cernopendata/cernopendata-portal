import logging
import uuid
from datetime import datetime

import gfal2
from invenio_accounts.models import User
from invenio_db import db
from invenio_files_rest.models import FileInstance
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql import func

from cernopendata.api import FileIndexMetadata, MultiURIFileObject, RecordFilesWithIndex
from cernopendata.modules.fixtures.cli import (
    create_record,
    delete_record,
    update_record,
)
from cernopendata.modules.records.minters.docid import cernopendata_docid_minter
from cernopendata.modules.records.minters.recid import cernopendata_recid_minter
from cernopendata.modules.records.minters.termid import cernopendata_termid_minter


class Release(db.Model):
    """Release model."""

    __tablename__ = "releases"

    STATUS_DRAFT = "DRAFT"
    STATUS_READY = "READY"
    STATUS_EDITING = "EDITING"
    STATUS_DEPLOYED = "DEPLOYED"
    STATUS_PUBLISHED = "PUBLISHED"

    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_DRAFT,
        index=True,
    )

    # --- Identifiers ---
    id = db.Column(db.Integer, primary_key=True)

    # --- Timestamps ---
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
    )
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id),
        nullable=False,
    )
    created_by = db.relationship(
        User,
        foreign_keys=[created_by_id],
        lazy="joined",
    )

    # --- last updater ---
    updated_by_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id),
        nullable=True,
    )

    updated_by = db.relationship(
        User,
        foreign_keys=[updated_by_id],
        lazy="joined",
    )

    experiment = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # --- Content ---
    json_fields = ["records", "documents", "glossary", "errors"]
    for f in json_fields:
        default = list if f == "errors" else dict
        locals()[f] = db.Column(
            JSONB, nullable=False, default=default
        )

    # --- Counters ---
    int_fields = [
        "num_records",
        "num_errors",
        "num_docs",
        "num_glossaries",
        "num_files",
        "num_file_indices",
    ]
    for f in int_fields:
        locals()[f] = db.Column(db.Integer, nullable=False, default=0)

    size_files = db.Column(
        db.BigInteger,
        nullable=False,
        default=0,
    )

    size_indexFiles = db.Column(
        db.BigInteger,
        nullable=False,
        default=0,
    )

    # --- Validation flags ---
    bool_fields = ["valid_recid", "valid_files", "valid_doi", "expanded_files"]
    for f in bool_fields:
        locals()[f] = db.Column(db.Boolean, nullable=False, default=False)

    max_recid = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    # --- Convenience helpers ---
    def _duplicate_file_uris(self):
        """Check that URIs in this release are not already persisted in the system."""
        uris = {
            f["uri"]
            for record in self.records
            for f in record.get("files", [])
            if "uri" in f
        }

        if not uris:
            return True  # nothing to check

        # Query ObjectVersion for existing URIs
        existing_files = FileInstance.query.filter(FileInstance.uri.in_(uris)).all()

        # Collect colliding URIs
        used_uris = {obj.uri for obj in existing_files}

        if used_uris:
            self.errors.append(
                f"The following file URIs are already stored in the system: "
                f"{', '.join(sorted(used_uris))}"
            )

    def _duplicate_pids(self):
        recids = [r.get("recid") for r in self.records if r.get("recid")]
        existing_pid = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == "recid",
            PersistentIdentifier.pid_value.in_(recids),
            PersistentIdentifier.status == "R",
        ).all()
        if existing_pid:
            used = [pid.pid_value for pid in existing_pid]
            self.errors.append(f"RECIDs already registered: {', '.join(used)}")
            self.valid_recid = False
            return used
        return []

    def validate(self, current_user=None):
        """
            Check if a release is ready to be published
        Checks:
        1. 'experiment' field exists, is a list, contains only expected_experiment
        2. Each record has 'title', 'recid', 'DOI'
        3. 'recid' and 'DOI' are unique across all entries

        Returns:
            invalid_entries: a list of dicts with 'entry_index' and 'errors'


        """
        self.num_records = len(self.records)
        self.num_files = 0
        self.num_file_indices = 0
        self.num_invalid_records = 0
        self.valid_recid = True
        self.valid_doi = True
        self.valid_files = True
        self.expanded_files = True
        self.errors = []
        recids = []
        for i, entry in enumerate(self.records):

            # --- Check experiment ---
            exp_list = entry.get("experiment")
            if exp_list is None:
                self.errors.append(f"Entry {i}: 'experiment' field is missing")
            elif not isinstance(exp_list, list):
                self.errors.append(f"Entry {i}: 'experiment' must be a list")
            elif any(exp != self.experiment.upper() for exp in exp_list):
                self.errors.append(
                    f"Entry {i+1}: 'experiment' must contain only '{self.experiment}'"
                )

            # --- Check required fields ---
            for field in ("title", "recid", "doi"):
                if field not in entry or not entry[field]:
                    self.errors.append(
                        f"Entry {i+1}: Missing or empty required field '{field}'"
                    )
                    if field == "recid":
                        self.valid_recid = False
                    if field == "doi":
                        self.valid_doi = False
            if "files" in entry:
                for j, file in enumerate(entry["files"]):
                    if not "uri" in file or "*" == file["uri"][-1:]:
                        self.errors.append(
                            f"Entry {i+1}, file {j+1}: The path is not expanded"
                        )
                        self.expanded_files = False
                    elif not "checksum" in file or not "size" in file:
                        self.errors.append(
                            f"Entry {i+1}, file {j+1}: Missing size/checksum"
                        )
                        self.valid_files = False
                    if "type" in file and file["type"] == "index.json":
                        self.num_file_indices += 1
                    else:
                        self.num_files += 1
            if "recid" in entry:
                recids.append(entry["recid"])

        if self.status in [Release.STATUS_DRAFT, Release.STATUS_READY]:
            self._duplicate_pids()
            self._duplicate_file_uris()
        flag_modified(self, "errors")
        self.num_errors = len(self.errors)
        if self.status == Release.STATUS_EDITING:
            if self.num_errors == 0:
                self.status = Release.STATUS_READY
            else:
                self.status = Release.STATUS_DRAFT
        if current_user:
            self.updated_by = current_user

    @classmethod
    def create(cls, *, experiment, records, created_by):
        """Create a new draft release"""
        if not isinstance(records, list):
            raise ValueError("records must be a list")
        release = cls(
            experiment=experiment,
            records=records,
            created_by=created_by,
            updated_by=created_by,
            status=Release.STATUS_DRAFT,
        )
        release.validate()

        db.session.add(release)

        db.session.commit()

        return release

    @classmethod
    def validate_experiment(cls, experiment):
        """Ensure that the requested experiment exists, and that the user has permission"""
        return experiment in {"lhcb", "opera", "alice", "atlas", "cms", "delphi"}

    def next_recid_start(self):
        """Return the next RECID counter for an experiment."""
        max_value = (
            db.session.query(func.max(self.max_recid))
            .filter(self.experiment == self.experiment)
            .scalar()
        )
        return (max_value or 0) + 1

    def generate_recids(self):
        """
        Assign RECIDs to all records in the release.
        RECID format: <experiment>-<counter>
        """
        if self.valid_recid:
            raise RuntimeError("RECIDs already generated")

        counter = self.next_recid_start()
        duplicates = self._duplicate_pids()

        for record in self.records:
            if "recid" not in record or record["recid"] in duplicates:
                counter += 1
                record["recid"] = f"{self.experiment}-{counter}"
                # This is to tell alchemy that the field has been modified
                flag_modified(self, "records")

        if self.records:
            self.max_recid = counter

        self.validate()

    def generate_doi(self):
        """
        Assign RECIDs to all records in the release.
        RECID format: <experiment>-<counter>
        """
        if self.valid_doi:
            raise RuntimeError("RECIDs already generated")

        for record in self.records:
            if "doi" not in record:
                record["doi"] = f"FAKE DOI FOR  {self.experiment}"
                # This is to tell alchemy that the field has been modified
                flag_modified(self, "records")
        self.validate()

    def _release_warning_html(self):
        return (
            "<div class='ui warning message release-warning'>"
            "WARNING: This record is part of a "
            f"<a href='/releases/{self.experiment}/{self.id}'>release</a> "
            "that has not been published yet. The entries do not appear in a normal search"
            "</div>"
        )

    def deploy(self, schema):
        if self.status != "READY":
            raise RuntimeError("Release is not READY")

        if not self.valid_recid:
            raise RuntimeError("RECIDs not generated")

        for record_data in self.records:
            record_data["$schema"] = schema
            if "abstract" not in record_data:
                record_data["abstract"] = {"description": ""}
            if "description" not in record_data["abstract"]:
                record_data["abstract"]["description"] = ""
            record_data["abstract"]["description"] = (
                self._release_warning_html() + record_data["abstract"]["description"]
            )
            record = create_record(record_data, False)
            record.commit()
        self.status = "DEPLOYED"

    def publish(self, schema):
        if self.status != "DEPLOYED":
            raise RuntimeError("Release is not DEPLOYED")

        indexer = RecordIndexer()
        for record_data in self.records:
            record_data["$schema"] = schema
            pid_object = PersistentIdentifier.get("recid", record_data["recid"])
            record = update_record(pid_object, record_data, True)
            record.commit()
            indexer.index(record)

        self.status = self.STATUS_PUBLISHED

    def generate_filemetadata(self):
        modified = False
        for record in self.records:
            if not "files" in record:
                continue
            for file in record["files"]:
                if "checksum" not in file:
                    file["checksum"] = "FAKE"
                    modified = True
                if "size" not in file:
                    file["size"] = "FAKE"
                    modified = True
        if modified:
            # This is to tell alchemy that the field has been modified
            flag_modified(self, "records")
            self.validate()
        return modified

    def rollback(self):
        if self.status not in ("DEPLOYED",):
            raise ValueError("Rollback not allowed in current state")

        for record_data in self.records:
            pid_object = PersistentIdentifier.get("recid", record_data["recid"])
            delete_record(pid_object, "recid")

        self.status = self.STATUS_READY

    def expand_files(self):
        import gfal2

        ctx = gfal2.creat_context()

        modified = False

        def walk(base_uri):
            """Recursively yield all file paths under base_uri"""
            try:
                print(f"LISTING {base_uri}", file=sys.stderr)
                entries = ctx.listdir(base_uri.replace("root://", "https://"))
            except gfal2.GError:
                self.errors.append(f"Error accessing the path {base_uri} while expanding the file names")
                print("GOT AN ERROR")
                return  # skip if inaccessible

            for entry in entries:
                full_uri = f"{base_uri}/{entry}"
                try:
                    st = ctx.stat(full_uri.replace("root://", "https://"))
                except gfal2.GError:
                    continue

                # If it’s a directory, recurse
                if st.st_mode & 0o40000:  # POSIX directory flag
                    yield from walk(full_uri)
                else:
                    # It's a file — yield uri, checksum, size
                    try:
                        checksum = ctx.checksum( full_uri.replace("root://", "https://"), "ADLER32")
                    except gfal2.GError:
                        checksum = "UNKNOWN"
                    yield {"uri": full_uri, "size": st.st_size, "checksum": checksum}

        import sys
        for record in self.records:
            if "files" not in record:
                continue

            new_files = []
            for file in record["files"]:
                if "uri" in file and file["uri"].endswith("*"):
                    basedir = file["uri"][:-1]
                    print("FOUND AN ENTRY WITH A WILDCARD", file=sys.stderr)
                    for f in walk(basedir):
                        new_files.append(f)
                    modified = True

            # Append new files and remove the wildcard entry
            if new_files:
                print("AND THE NEW FILES", file=sys.stderr)

                # Remove the wildcard entry itself
                record["files"] = [
                    f
                    for f in record["files"]
                    if not (f.get("uri") and f["uri"].endswith("*"))
                ]
                record["files"].extend(new_files)
                print(record['files'], file=sys.stderr)

        import sys
        print("WE HAD")
        print(self.errors, file=sys.stderr)
        if modified:
            flag_modified(self, "records")
            self.validate()

        return modified

    def lock_for_editing(self):
        """
        Acquire a DB row lock and mark this release as EDITING.
        """
        try:
            # Re-lock THIS row in the database
            db.session.query(Release).filter_by(id=self.id).with_for_update(
                nowait=True, of=Release
            ).one()
        except OperationalError:
            return False

        if self.status == self.STATUS_EDITING:
            return False

        self.status = self.STATUS_EDITING
        db.session.commit()
        return True

    def update_records(self, records):
        self.records = records
        self.validate()
