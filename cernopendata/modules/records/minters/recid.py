"""PID minters."""

from invenio_oaiserver.provider import OAIIDProvider

from ..providers.recid import RecordUUIDProvider


def cernopendata_recid_minter(record_uuid, data):
    """Mint deposit's PID."""
    if "id" in data:
        recid = data["id"]
    else:
        recid = data["recid"]

    provider = RecordUUIDProvider.create(
        object_type="rec",
        pid_type="recid",
        object_uuid=record_uuid,
        pid_value=str(recid),
    )

    data["pids"] = {"oai": {"id": f"oai:cernopendata.cern:{recid}"}}

    OAIIDProvider.create(
        object_type="rec",
        object_uuid=record_uuid,
        pid_value=f"oai:cernopendata.cern:{recid}",
    )

    return provider.pid
