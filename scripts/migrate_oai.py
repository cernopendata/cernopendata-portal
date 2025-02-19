# This script will be used for the introduction of the OAI-PMH interface.
# The entries that have already been inserted in the repository are missing a new PID (OAIIDProvider),
# and the json object should contain also the oaid
# New entries will have those fields, thanks to the changes in the minter of the recid, which also creates the OAIID

from invenio_db import db
from invenio_oaiserver.provider import OAIIDProvider
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_search.proxies import current_search_client

counter=0
for entry in PersistentIdentifier.query.filter_by(pid_type="recid").all():
    # First, let's create all the PID
    new_pid = OAIIDProvider.create(
        object_type="rec",
        object_uuid=entry.object_uuid,
        pid_value=f"oai:cernopendata.cern:{entry.pid_value}",
    )
    #    db.session.add(new_pid)

    # Now, let's make sure that all the entries have the oai pid set as well
    a = db.session.get(RecordMetadata, entry.object_uuid)
    a.data = a.data | {
        "pids": {"oai": {"id": f'oai:cernopendata.cern:{a.json["recid"]}'}}
    }
    counter+=1
    counter%50 or print(".", end='')
    counter%1000 or print(counter)

db.session.commit()


# Last thing, let's update also the opensearch entries:
current_search_client.update_by_query(
    "opendata-*-records-record-v1.0.0",
    {
        "script": {
            "source": "ctx._source.pids = ['oai': ['id' : 'oai:cernopendata.cern:' + ctx._source.recid]] ;",
            "lang": "painless",
        }
    },
)
print("DONE")
