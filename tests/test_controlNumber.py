from unittest.mock import MagicMock

import pytest
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record

from cernopendata.modules.fixtures.cli import (
    create_glossary_term,
    delete_doc_or_glossary,
    update_doc_or_glossary,
)


def test_update_doc(app, database):
    print("Checking if t_number is there after an update")

    data = {
        "anchor": "dummy_anchor",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
        "category": "value_to_delete",
    }

    record = create_glossary_term(data, False)
    print("Record created")
    print(record)

    assert record["category"]

    pid_object = PersistentIdentifier.get("termid", "dummy_anchor")
    new_data = {
        "anchor": "dummy_anchor",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
        "accelerator": "value_to_keep",
    }
    record = update_doc_or_glossary(pid_object, new_data, False)
    print("Record updated")
    print(record)
    assert "category" not in record.keys()
    assert record["accelerator"]

    delete_doc_or_glossary(pid_object, "termid")
    database.session.commit()

    with pytest.raises(PIDDoesNotExistError):
        PersistentIdentifier.get("termid", "dummy_anchor")


def test_delete_term_already_gone(app, database):
    """Deleting a glossary term whose record is already gone."""
    data = {
        "anchor": "orphaned_anchor",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
        "category": "value_to_delete",
    }

    create_glossary_term(data, False)
    pid_object = PersistentIdentifier.get("termid", "orphaned_anchor")
    Record.get_record(pid_object.object_uuid).delete()
    database.session.commit()

    logger = MagicMock()
    delete_doc_or_glossary(pid_object, "termid", logger=logger)
    database.session.commit()

    assert "orphaned_anchor" in logger.warning.call_args[0][0]
    with pytest.raises(PIDDoesNotExistError):
        PersistentIdentifier.get("termid", "orphaned_anchor")
