# This script is used to populate the num_record_files and record_size columns
# of RequestMetadata to ensure the transfer statistics table has all relevant
# information
# Run the script via cernopendata shell /code/scripts/migrate_request_data.py

from invenio_db import db
from sqlalchemy.orm import Session

from cernopendata.api import RecordFilesWithIndex
from cernopendata.cold_storage.models import RequestMetadata

BATCH_SIZE = 1000

print("Starting script...")

query = RequestMetadata.query.filter_by(
    num_record_files=None, record_size=None
).order_by(RequestMetadata.id)

print("Processing requests in batches of {BATCH_SIZE}")

counter = 1

with db.engine.connect() as connection:
    print(f"Processing batch {counter // BATCH_SIZE}...")
    read_session = Session(bind=connection)
    stream_results = read_session.execute(
        query.statement, execution_options={"yield_per": BATCH_SIZE}
    )

    for row in stream_results:
        request = db.session.merge(row[0])

        print(f" - Processsing transfer request {request.id}")

        record = RecordFilesWithIndex.get_record(request.record_id)
        distribution = record.get("distribution")

        if distribution:
            request.num_record_files = distribution.get("number_files")
            request.record_size = distribution.get("size")

        if counter % BATCH_SIZE == 0:
            print(f"Commiting changes for batch {counter // BATCH_SIZE}...")
            db.session.commit()

        counter += 1

print("Commiting final changes...")
db.session.commit()
print("Script completed")
