"""News endpoint accessible via the CERN Open Data Portal API."""

from datetime import datetime

from flask import Blueprint, Response, request

from ..pages.utils import FeaturedArticlesSearch

blueprint = Blueprint("cernopendata_api_news", __name__)


@blueprint.route("/news.xml", methods=["GET"])
def get_latest_news():
    """Returns the set amount of latest news from the Open Data Portal."""
    limit = request.args.get("limit", default=10, type=int)
    limit = min(abs(limit), 128)

    try:
        news = (
            FeaturedArticlesSearch().sort("-date_published")[:limit].execute().hits.hits
        )
    except Exception:
        news = []

    rss_items = "\n".join(
        [
            f"""
            <item>
                <title>{article.get("title", "CERN Open Data update")}</title>
                <link>
                    https://opendata.cern.ch/docs/{article.get("slug", "")}
                </link>
                <pubDate>{
                    datetime.strptime(article.get("date_published", "2000-01-01"), "%Y-%m-%d")
                    .strftime("%a, %d %b %Y 00:00:00 +0000")
                }</pubDate>
                <description>
                    Author: {article.get("author", "Open Data Portal team")}
                </description>
            </item>
            """
            for a in news
            if (article := a.get("_source"))
        ]
    )

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
        <channel>
            <title>CERN Open Data RSS News</title>
            <link>https://opendata.cern.ch/</link>
            <description>
                Latest news from CERN Open Data
            </description>
            <language>en</language>
            {rss_items}
        </channel>
    </rss>
    """

    return Response(rss_feed, mimetype="application/xml")
