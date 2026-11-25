# This script populates the pidstore_pid table with an <experiment>-<recid> alias
# for every existing recid PID, so both the old and new recid format resolve to the record.
# Run the script via cernopendata shell /code/scripts/migrate_recid_aliases.py

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from sqlalchemy.orm import Session

BATCH_SIZE = 1000

print("Starting script...")

query = (
    db.session.query(
        PersistentIdentifier.pid_value,
        PersistentIdentifier.object_uuid,
        RecordMetadata.json["experiment"],
    )
    .outerjoin(RecordMetadata, PersistentIdentifier.object_uuid == RecordMetadata.id)
    .filter(PersistentIdentifier.pid_type == "recid")
    .filter(PersistentIdentifier.pid_value.op("~")(r"^[0-9]+$"))
    .order_by(PersistentIdentifier.id)
)

existing_aliases = {
    value
    for (value,) in db.session.query(PersistentIdentifier.pid_value)
    .filter(PersistentIdentifier.pid_type == "recid")
    .filter(PersistentIdentifier.pid_value.op("~")("[^0-9]"))
}

print(f"Processing recid PIDs in batches of {BATCH_SIZE}")

created = 0
skipped_existing_alias = 0
error = []

counter = 1

with db.engine.connect() as connection:
    read_session = Session(bind=connection)
    stream_results = read_session.execute(
        query.statement, execution_options={"yield_per": BATCH_SIZE}
    )

    for pid_value, object_uuid, experiments in stream_results:
        if not experiments:
            error.append(pid_value)
            counter += 1
            continue

        # Records with multiple experiments get one alias per experiment.
        for experiment in experiments:
            new_value = f"{experiment.lower()}-{pid_value}"

            if new_value in existing_aliases:
                skipped_existing_alias += 1
                continue

            print(f" - Creating recid alias {new_value} -> {pid_value}")
            db.session.add(
                PersistentIdentifier(
                    pid_type="recid",
                    pid_value=new_value,
                    object_type="rec",
                    object_uuid=object_uuid,
                    status=PIDStatus.REGISTERED,
                )
            )
            existing_aliases.add(new_value)
            created += 1

        if counter % BATCH_SIZE == 0:
            print(f"Commiting changes for batch {counter // BATCH_SIZE}...")
            db.session.commit()

        counter += 1

print("Commiting final changes...")
db.session.commit()

print("Script completed")
print(f" - Aliases created: {created}")
print(f" - Skipped (alias already existed): {skipped_existing_alias}")
print(f" - Failed to create new format: {len(error)}")
for pid_value in error:
    print(f"     recid {pid_value}")
