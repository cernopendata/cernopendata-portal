"""Tests for the display experiment exclusion feature."""

import pytest
from bs4 import BeautifulSoup
from invenio_indexer.api import RecordIndexer

from cernopendata.modules.fixtures.cli import create_doc
from cernopendata.modules.pages.views import index


def test_news(app, database, search):
    """Test that news are displayed properly."""
    # Let's start by inserting a news item
    data = {
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            "records/docs-v1.0.0.json"
        ),
        "type": {"primary": "news"},
        "slug": "dummy_news",
        "date_published": "2024-11-27",
        "featured": 1,
        "title": "DUMMY TEST NEWS",
    }
    record = create_doc(data, True)

    RecordIndexer().index(record, arguments={"refresh": "wait_for"})
    with app.test_request_context("/"):
        soup = BeautifulSoup(index(), "html.parser")
        news = soup.find_all("div", class_="news-card")
        assert len(news) == 1
        assert news[0].h4.a["href"] == "/docs/dummy_news"
