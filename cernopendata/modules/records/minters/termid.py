"""PID minters."""

from ..providers.termid import TermUUIDProvider

from .opendata import cernopendata_generic_minter


def cernopendata_termid_minter(record_uuid, data):
    """Mint deposit's PID."""

    return cernopendata_generic_minter(
        record_uuid, data, "termid", "anchor", TermUUIDProvider
    )
