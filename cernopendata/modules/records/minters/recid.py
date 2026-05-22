"""PID minters."""

from ..providers.recid import RecordUUIDProvider
from .opendata import cernopendata_generic_minter


def cernopendata_recid_minter(record_uuid, data):
    """Mint deposit's PID."""
    return cernopendata_generic_minter(
        record_uuid, data, "recid", "recid", RecordUUIDProvider, oai=True
    )
