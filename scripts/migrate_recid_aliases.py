# This script populates the pidstore_pid table with an <experiment>-<recid> alias
# for every existing recid PID, so both the old and new recid format resolve to the record.
# Run the script via cernopendata shell /code/scripts/migrate_recid_aliases.py

from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from sqlalchemy.orm import Session

BATCH_SIZE = 1000

print("Starting script...")

query = PersistentIdentifier.query.filter_by(pid_type="recid").order_by(
    PersistentIdentifier.id
)

print(f"Processing recid PIDs in batches of {BATCH_SIZE}")

created = 0
skipped_already_new = 0
skipped_existing_alias = 0
error = []

counter = 1

with db.engine.connect() as connection:
    read_session = Session(bind=connection)
    stream_results = read_session.execute(
        query.statement, execution_options={"yield_per": BATCH_SIZE}
    )

    for row in stream_results:
        existing_pid = db.session.merge(row[0])
        pid_value = existing_pid.pid_value

        if not pid_value.isdigit():
            skipped_already_new += 1
            counter += 1
            continue

        record = db.session.get(RecordMetadata, existing_pid.object_uuid)
        experiments = (record.json or {}).get("experiment") if record else None

        if not experiments:
            error.append(pid_value)
            counter += 1
            continue

        # Records with multiple experiments get one alias per experiment.
        for experiment in experiments:
            new_value = f"{experiment.lower()}-{pid_value}"

            try:
                PersistentIdentifier.get("recid", new_value)
                skipped_existing_alias += 1
            except PIDDoesNotExistError:
                print(f" - Creating recid alias {new_value} -> {pid_value}")
                PersistentIdentifier.create(
                    "recid",
                    new_value,
                    object_type="rec",
                    object_uuid=existing_pid.object_uuid,
                    status=PIDStatus.REGISTERED,
                )
                created += 1

        if counter % BATCH_SIZE == 0:
            print(f"Commiting changes for batch {counter // BATCH_SIZE}...")
            db.session.commit()

        counter += 1

print("Commiting final changes...")
db.session.commit()

print("Script completed")
print(f" - Aliases created: {created}")
print(f" - Skipped (already new format): {skipped_already_new}")
print(f" - Skipped (alias already existed): {skipped_existing_alias}")
print(f" - Failed to create new format: {len(error)}")
for pid_value in error:
    print(f"     recid {pid_value}")
