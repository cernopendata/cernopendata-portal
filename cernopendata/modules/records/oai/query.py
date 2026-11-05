"""CERN Open Data OAI interface."""

from invenio_search import RecordsSearch
from invenio_search.engine import dsl


class OAIServerSearch(RecordsSearch):
    """Define default filter for querying OAI server."""

    class Meta:
        """Configuration for OAI server search."""

        # Every version of an entry keeps the same 'pids.oai.id', which is the
        # concept OAI identifier and resolves to the latest version. The old
        # versions are therefore excluded, so that the identifier is unique.
        default_filter = dsl.Q("exists", field="pids.oai.id") & ~dsl.Q(
            "term", **{"_versions.is_latest": False}
        )
