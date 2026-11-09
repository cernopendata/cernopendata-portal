import os
import zlib

from invenio_db import db
from invenio_indexer.api import RecordIndexer

from cernopendata.cold_storage.models import Location
from cernopendata.modules.fixtures.cli import create_record

recid = "900000"
file_names = ["cold-test-file-1.txt", "cold-test-file-2.txt"]

location = Location.query.filter(
    Location.manager_class.like("%cp.TransferManager")
).first()

if not location:
    raise SystemExit(
        "No local cold storage location found. Populate the instance with "
        "scripts/populate-instance.sh --local-cold-storage"
    )

files = []
for file_name in file_names:
    content = f"Dummy content of {file_name} for cold storage testing.".encode()
    file_path = os.path.join(location.hot_path, file_name)
    with open(file_path, "wb") as dummy_file:
        dummy_file.write(content)
    files.append(
        {
            "uri": file_path,
            "size": len(content),
            "checksum": f"adler32:{zlib.adler32(content):08x}",
        }
    )

record = create_record(
    {
        "$schema": "https://opendata.cern.ch/schema/records/record-v1.0.0.json",
        "recid": recid,
        "title": f"Cold storage test record {recid}",
        "date_published": "2026",
        "experiment": ["ALICE"],
        "publisher": "CERN Open Data Portal",
        "type": {"primary": "Dataset", "secondary": ["Derived"]},
        "files": files,
        "distribution": {
            "size": sum(file["size"] for file in files),
            "formats": ["txt"],
            "number_files": len(files),
        },
    },
    False,
)
record.commit()
db.session.commit()
RecordIndexer().index(record)

print(f"Record {recid} created with {len(files)} files under {location.hot_path}")
