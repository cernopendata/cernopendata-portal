"""PID Fetchers."""

from collections import namedtuple

from ..providers.recid import RecordUUIDProvider
from ..providers.termid import TermUUIDProvider
from ..providers.docid import DocUUIDProvider

from invenio_oaiserver.provider import OAIIDProvider
from invenio_pidstore.models import PIDStatus

FetchedPID = namedtuple("FetchedPID", ["provider", "pid_type", "pid_value"])


def cernopendata_recid_fetcher(record_uuid, data):
    """Fetch a term's identifiers."""
    return FetchedPID(
        provider=RecordUUIDProvider,
        pid_type=RecordUUIDProvider.pid_type,
        pid_value=data["recid"],
    )


def cernopendata_generic_fetcher(record_uuid, data):
    """Fetch a term's identifiers."""
    if "recid" in data:
        return FetchedPID(
            provider=RecordUUIDProvider,
            pid_type=RecordUUIDProvider.pid_type,
            pid_value=data["recid"],
        )
    if "anchor" in data:
        return FetchedPID(
            provider=TermUUIDProvider,
            pid_type=TermUUIDProvider.pid_type,
            pid_value=data["anchor"],
        )
    if "slug" in data:
        return FetchedPID(
            provider=DocUUIDProvider,
            pid_type=DocUUIDProvider.pid_type,
            pid_value=data["slug"],
        )


def cernopendata_oai_fetcher(record_uuid, data):
    """Fetch a term's identifiers."""
    pid = FetchedPID(
        provider=OAIIDProvider,
        pid_type=OAIIDProvider.pid_type,
        pid_value=data["pids"]["oai"]["id"],
    )

    return pid
