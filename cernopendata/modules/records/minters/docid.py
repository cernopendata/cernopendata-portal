"""PID minters."""

from ..providers.docid import DocUUIDProvider
from .opendata import cernopendata_generic_minter


def cernopendata_docid_minter(record_uuid, data):
    """Mint deposit's PID."""
    return cernopendata_generic_minter(
        record_uuid, data, "docid", "slug", DocUUIDProvider
    )
