"""CERN Open Data OAI interface."""

from invenio_search import RecordsSearch
from invenio_search.engine import dsl


class OAIServerSearch(RecordsSearch):
    """Define default filter for querying OAI server."""

    class Meta:
        """Configuration for OAI server search."""

        default_filter = dsl.Q("exists", field="pids.oai.id")
