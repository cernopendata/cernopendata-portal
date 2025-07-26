"""Record search factory."""

from flask import request
from invenio_records_rest.query import es_search_factory


def search_factory(*args):
    """Custom search factory that skips files if requested."""
    search, urlkwargs = es_search_factory(*args)

    if "skip_files" in request.args:
        search = search.source(exclude=["files", "_file_indices", "_files"])
        urlkwargs.add("skip_files", "1")

    return search, urlkwargs
