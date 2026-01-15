# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2024 CERN.
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

"""CERN Open Data Release api."""

import json
from copy import deepcopy
from datetime import datetime

from deepdiff import DeepDiff
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from cernopendata.modules.fixtures.cli import (
    create_record,
    delete_record,
    update_record,
)

from .models import (
    ReleaseHistory,
    ReleaseMetadata,
    ReleaseStatus,
    ReleaseValidationMetadata,
)
from .validations import VALIDATIONS
from .validations.base import Validation


class ReleaseValidation:
    """Validation results for a release."""  #

    def __init__(self, metadata):
        """Create a ReleaseValidation."""
        self._metadata = metadata
        self.validator = next(
            (v() for v in Validation.registry if v.name == self.name), None
        )

    @property
    def fixable(self):
        """Check if a validation can be fixed automatically."""
        return self.validator.fixable

    @property
    def error_message(self):
        """Error message that should be presented."""
        return self.validator.error_message

    @property
    def optional(self):
        """Boolean to check if the validation is optional."""
        return self.validator.optional

    @property
    def name(self):
        """Name of the validation."""
        return self._metadata.name

    @property
    def status(self):
        """Status of the validation."""
        return self._metadata.status

    def set_status(self, status):
        """Put the status of the validation."""
        self._metadata.status = status

    @property
    def enabled(self):
        """Return if the validation is enabled for this particular release."""
        return self._metadata.enabled

    @classmethod
    def get(cls, release_id, name):
        """Get a particular validation from the release and validation name."""
        metadata = ReleaseValidationMetadata.query.filter_by(
            id=release_id, name=name
        ).first()

        return cls(metadata)

    def validate(self):
        """Run the validation."""
        return self.validator.validate(self._metadata.release)

    def fix(self):
        """Execute the fix for a validation."""
        return self.validator.fix(self._metadata.release)

    def to_dict(self):
        """Convert into a dictionary."""
        return {
            "id": self._metadata.id,
            "name": self.name,
            "enabled": self.enabled,
            "optional": self.optional,
            "status": self.status,
            "error_message": self.error_message,
            "release_id": self._metadata.release_id,
        }

    @classmethod
    def get(cls, validation_id):
        """Get a release from the database."""
        metadata = ReleaseValidationMetadata.query.filter_by(
            id=validation_id,
        ).first()

        return cls(metadata)


class Release:
    """Class for the release."""

    record_schema = "local://records/record-v1.0.0.json"

    def __init__(self, metadata):
        """Initialize the object."""
        self._metadata = metadata

    @property
    def status(self):
        """Status of the release."""
        return self._metadata.status

    @property
    def records(self):
        """Records of the release."""
        return self._metadata.records

    @property
    def validations(self):
        """Validation object."""
        return [ReleaseValidation(v) for v in self._metadata.validations]

    @classmethod
    def create(
        cls, *, experiment, records, current_user, name=None, discussion_url=None
    ):
        """Create a new draft release."""
        if not isinstance(records, list):
            raise ValueError("records must be a list")
        release = ReleaseMetadata(
            name=name,
            discussion_url=discussion_url,
            experiment=experiment,
            records=records,
            status=ReleaseStatus.DRAFT.value,
        )
        obj = cls(release)
        obj.validate(current_user)
        obj.create_validations()
        db.session.add(release)

        db.session.commit()

        return obj

    def create_validations(self):
        """Initializes the validations for a release."""
        for validation in VALIDATIONS:
            if (
                validation.experiment
                and validation.experiment != self._metadata.experiment
            ):
                continue
            new_validation = ReleaseValidationMetadata(
                release=self._metadata,
                name=validation.name,
                status=False,
                enabled=not validation.optional,
            )
            self._metadata.validations.append(new_validation)
            db.session.add(new_validation)

    @classmethod
    def list_releases(cls, experiment):
        """Return all the releases for a given experiment."""
        return (
            db.session.query(ReleaseMetadata)
            .options(
                selectinload(ReleaseMetadata.history_events).selectinload(
                    ReleaseHistory.user
                )
            )
            .filter(ReleaseMetadata.experiment == experiment)
            .order_by(ReleaseMetadata.id.desc())
            .all()
        )

    @classmethod
    def validate_experiment(cls, experiment):
        """Ensure that the requested experiment exists."""
        return experiment in {"lhcb", "opera", "alice", "atlas", "cms", "delphi"}

    @classmethod
    def get(cls, experiment, release_id):
        """Get a release from the database."""
        metadata = ReleaseMetadata.query.filter_by(
            id=release_id, experiment=experiment
        ).first()

        return cls(metadata)

    def is_status(self, status):
        """Check if the release is in a particular status."""
        if isinstance(status, (list, tuple, set)):
            return self.status in [s for s in status]
        return self._metadata.status == status

    def lock(self, status, lock_status, current_user):
        """Acquire a DB row lock and mark this release as EDITING."""
        try:
            db.session.query(ReleaseMetadata).filter_by(
                id=self._metadata.id
            ).with_for_update(nowait=True, of=ReleaseMetadata).one()
        except OperationalError:
            return False
        if status and not self.is_status(status):
            return False

        self.change_status(lock_status, current_user)
        db.session.commit()
        return True

    def change_status(self, status, current_user):
        """Change the status of the releases."""
        event = ReleaseHistory(
            release=self._metadata,
            status=status.value,
            timestamp=datetime.utcnow(),
            user_id=current_user.id,
        )
        self._metadata.status = status.value
        db.session.add(event)
        return event

    def delete(self):
        """Delete a release."""
        db.session.delete(self._metadata)
        db.session.commit()

    def update_records(self, records, current_user):
        """Update the records of a release."""
        self._metadata.records = records
        self.validate(current_user)
        db.session.add(self._metadata)
        db.session.commit()

    def validate(self, current_user):
        """
            Check if a release is ready to be published.

        Checks:
        1. 'experiment' field exists, is a list, contains only expected_experiment
        2. Each record has 'title', 'recid', 'DOI'
        3. 'recid' and 'DOI' are unique across all entries

        Returns:
            invalid_entries: a list of dicts with 'entry_index' and 'errors'


        """
        self._metadata.num_records = len(self._metadata.records)
        self._metadata.num_files = 0
        self._metadata.num_file_indices = 0
        self._metadata.errors = []

        for validation in self.validations:
            if validation.enabled:
                errors = validation.validate()
                if errors:
                    self._metadata.errors.extend(errors)
                validation.set_status(len(errors) == 0)
                db.session.add(validation._metadata)

        for i, entry in enumerate(self._metadata.records):

            if "files" in entry:
                for j, file in enumerate(entry["files"]):
                    if "uri" not in file or "*" == file["uri"][-1:]:
                        self._metadata.errors.append(
                            f"Entry {i + 1}, file {j + 1}: The path is not expanded"
                        )
                        validations["expanded_files"] = False
                    if "type" in file and file["type"] == "index.json":
                        self._metadata.num_file_indices += 1
                    else:
                        self._metadata.num_files += 1

        flag_modified(self._metadata, "records")
        flag_modified(self._metadata, "errors")
        self._metadata.num_errors = len(self._metadata.errors)
        if self._metadata.num_errors == 0:
            self.change_status(ReleaseStatus.READY, current_user)
        else:
            self.change_status(ReleaseStatus.DRAFT, current_user)

    def stage(self, schema, current_user):
        """Stage the entries of a release."""
        if not self.is_status(ReleaseStatus.STAGING):
            raise RuntimeError("Release is not READY")

        for record_data in self._metadata.records:
            record_data["$schema"] = Release.record_schema
            if "abstract" not in record_data:
                record_data["abstract"] = {"description": ""}
            if "description" not in record_data["abstract"]:
                record_data["abstract"]["description"] = ""
            record_data["prerelease"] = (
                f"{self._metadata.experiment}/{self._metadata.id}"
            )
            record = create_record(record_data, False)
            record.commit()
        self.change_status(ReleaseStatus.STAGED, current_user)
        db.session.add(self._metadata)
        db.session.commit()

    def publish(self, current_user):
        """Publish a release."""
        if not self.is_status(ReleaseStatus.STAGED):
            raise RuntimeError("Release is not STAGED")

        indexer = RecordIndexer()
        for record_data in self._metadata.records:
            record_data["$schema"] = Release.record_schema
            pid_object = PersistentIdentifier.get("recid", record_data["recid"])
            record = update_record(pid_object, record_data, True)
            record.commit()
            indexer.index(record)
        self.change_status(ReleaseStatus.PUBLISHED, current_user)
        db.session.add(self._metadata)
        db.session.commit()

    def rollback(self, current_user):
        """Remove the STAGED entries of a release."""
        if not self.is_status(ReleaseStatus.STAGED):
            raise RuntimeError("Release is not STAGED")

        for record_data in self._metadata.records:
            pid_object = PersistentIdentifier.get("recid", record_data["recid"])
            delete_record(pid_object, "recid")

        self.change_status(ReleaseStatus.READY, current_user)
        db.session.add(self._metadata)
        db.session.commit()

    def bulk_preview(self, updates, max_preview=10):
        """Preview the changes of a bulk update."""
        diffs = []

        for idx, record in enumerate(self._metadata.records[:max_preview]):
            original = record
            modified = deepcopy(record)

            # Apply ops to COPY
            if "set" in updates:
                for key, value in updates["set"].items():
                    if key in ReleaseMetadata.BULK_IMMUTABLE_FIELDS:
                        continue
                    modified[key] = value
            if "delete" in updates:
                for key in updates["delete"]:
                    if key in ReleaseMetadata.BULK_IMMUTABLE_FIELDS:
                        continue
                    modified.pop(key, None)

            diff = DeepDiff(
                original,
                modified,
                ignore_order=True,
            ).to_json()
            if diff:
                diffs.append(
                    {
                        "index": idx,
                        "recid": record.get("recid"),
                        "diff": json.loads(
                            diff
                        ),  # The to_json and json.loads is to make sure that the object can be jsonify
                    }
                )
        return diffs

    def bulk_update(self, updates, current_user):
        """Apply a bulk update to the records of a release."""
        records_modified = 0
        for record in self._metadata.records:
            modified = False
            if "set" in updates:
                for key, value in updates["set"].items():
                    if key in ReleaseMetadata.BULK_IMMUTABLE_FIELDS:
                        continue
                    record[key] = value
                    modified = True
            if "delete" in updates:
                for key in updates["delete"]:
                    if key in ReleaseMetadata.BULK_IMMUTABLE_FIELDS:
                        continue
                    if key in record:
                        del record[key]
                        modified = True
            if modified:
                records_modified += 1

        if records_modified:
            flag_modified(self._metadata, "records")
        self.validate(current_user)

        db.session.add(self._metadata)
        db.session.commit()

        return records_modified

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

    def fix_checks(self, current_user):
        """Fix all the validations that can be fixed automatically."""
        errors = []
        for validation in self.validations:
            if not validation.status:
                if validation.enabled and validation.fixable:
                    errors.extend(validation.fix())

        if errors:
            self._metadata.errors = errors
            self.change_status(ReleaseStatus.DRAFT, current_user)
        else:
            self.validate(current_user)
        flag_modified(self._metadata, "records")
        db.session.add(self._metadata)
        db.session.commit()

    def enable_validation(self, validation_id, enabled, current_user):
        """Enables or disables a partircular validation."""
        validation = ReleaseValidation.get(validation_id)

        if not validation.optional:
            raise RunTimeError(f"The validation {validation.name} can't be disabled")
        validation._metadata.enabled = enabled
        self.validate(current_user)
        db.session.add(validation._metadata)
        db.session.commit()
