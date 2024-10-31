import pytest
from invenio_pidstore.models import PersistentIdentifier

from cernopendata.modules.fixtures.cli import (
    create_glossary_term,
    update_doc_or_glossary,
)


def test_update_doc(app, database):
    print("Checking if the control_number is there after an update")
    data = {
        "anchor": "dummy_control_number",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
        "old_field": "value_to_delete",
    }

    record = create_glossary_term(data, False)
    print("Record created")
    print(record)
    assert record["control_number"]
    assert record["old_field"]

    pid_object = PersistentIdentifier.get("termid", "dummy_control_number")
    new_data = {
        "anchor": "dummy_control_number",
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/glossary-term-v1.0.0.json"
        ),
        "new_field": "value_to_keep",
    }
    record = update_doc_or_glossary(pid_object, new_data, False)
    print("Record updated")
    print(record)
    assert record["control_number"]
    assert "old_field" not in record.keys()
    assert record["new_field"]
