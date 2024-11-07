"""PID minters."""

from ..providers.docid import DocUUIDProvider


def cernopendata_docid_minter(record_uuid, data):
    """Mint deposit's PID."""
    provider = DocUUIDProvider.create(
        object_type="rec",
        pid_type="docid",
        object_uuid=record_uuid,
        pid_value=data["slug"],
    )

    return provider.pid
