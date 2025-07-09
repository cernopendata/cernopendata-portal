# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2018 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Sitemap generation for CERN Open Data Portal."""

from flask import current_app, render_template

from . import config
from .generators import sitemap_page_urls, yield_urls


class CERNOpenDataSitemap:
    """CERN Open Data sitemap extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        # Follow the Flask guidelines on usage of app.extensions
        if "cernopendata-sitemap" in app.extensions:
            raise RuntimeError("CERNOpenDataSitemap application already initialized")

        self.init_config(app)
        app.extensions["cernopendata-sitemap"] = self

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("CERNOPENDATA_SITEMAP_"):
                app.config.setdefault(k, getattr(config, k))

    @staticmethod
    def _generate_sitemap_urls(page):
        """Run all generators and yield the sitemap JSON entries."""
        start = page * config.CERNOPENDATA_SITEMAP_PAGE_SIZE
        limit = config.CERNOPENDATA_SITEMAP_PAGE_SIZE

        doc_types = current_app.config["CERNOPENDATA_SITEMAP_DOC_TYPES"]
        yield from yield_urls(doc_types, offset=start, limit=limit)

    def get_populated_sitemap(self, page):
        """Populate the sitemap template with current app urls."""
        site_url = current_app.config["SITE_URL"]
        with current_app.test_request_context(base_url=site_url):
            urls = iter(self._generate_sitemap_urls(page))
            return render_template("sitemap/sitemap_page.xml", urlset=iter(urls))

    @staticmethod
    def get_sitemap_list():
        """Return the list of all available sitemaps."""
        site_url = current_app.config["SITE_URL"]
        with current_app.test_request_context(base_url=site_url):
            doc_types = current_app.config["CERNOPENDATA_SITEMAP_DOC_TYPES"]
            urls = sitemap_page_urls(doc_types)

            return render_template("sitemap/sitemap_list.xml", urls=iter(urls))
