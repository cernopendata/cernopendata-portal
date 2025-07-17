# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017, 2018, 2021, 2022, 2023, 2024 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Open Data Portal; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""CERN Open Data Portal instance."""

import os

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

# Get the version string. Cannot be done with import!
g = {}
try:
    with open(os.path.join("cernopendata", "version.py"), "rt") as fp:
        exec(fp.read(), g)
        version = g["__version__"]
except FileNotFoundError:
    version = None

tests_require = [
    "check-manifest>=0.25",
    "coverage>=4.0",
    "isort>=4.2.2",
    "locustio>=0.8,<0.13",
    "mock>=1.3.0",
    "pydocstyle>=1.0.0",
    "pycodestyle>=2.4.0",
    "pytest-cache>=1.0",
    "pytest-cov==4.1.0",
    "pytest==7.4.4",
    "beautifulsoup4==4.12.3",
]

extras_require = {
    "docs": [
        "Sphinx==7.2.6",
    ],
    "tests": tests_require,
}

extras_require["all"] = []
for reqs in extras_require.values():
    extras_require["all"].extend(reqs)

setup_requires = [
    "pytest-runner>=2.6.2",
]

install_requires = [
    "counter-robots>=2025.2",
    # General Invenio dependencies
    "invenio-app>=2.0.0,<3.0.0",
    "invenio-base>=2.0.0,<3.0.0",
    "invenio-config>=1.0.3,<2.0.0",
    # Custom Invenio `base` bundle
    "importlib-metadata>=6.11.0",
    "invenio-accounts>=6.0.0,<7.0.0",
    "invenio-access>=4.0.0,<5.0.0",
    "invenio-files-rest @git+https://github.com/psaiz/invenio-files-rest@tag_value#egg=invenio-files-rest",
    "invenio-theme>=4.0.0,<5.0.0",
    "invenio-records>=3.0.0,<4.0.0",
    "invenio-records-rest[datacite]>=3.0.0,<4.0.0",
    "invenio-records-ui>=2.0.0,<3.0.0",
    "invenio-search-ui>=4.0.0,<5.0.0",
    "invenio-records-files>=1.2.1,<3.0.0",
    "invenio-stats>=5.1.0,<6.0.0",
    "jupyter-client==7.1.0",
    "invenio-jsonschemas>=2.0.0,<3.0.0",
    "pluggy==0.13.1",
    # Version 3.3.1 rolls back the changes of 3.2.0 :(. Waiting for at least 3.4...
    "invenio-oaiserver==3.2.0",
    # Custom Invenio `postgresql` bundle
    "invenio-db[versioning,postgresql]>=2.0.0,<3.0.0",
    "invenio-mail>=2.1.1",
    # Custom Invenio `opensearch` bundle
    "invenio-search[opensearch2]>=3.0.0,<4.0.0",
    # Specific Invenio dependencies
    "invenio-xrootd==2.0.0a1",
    "xrootdpyfs==2.0.0a1",
    # Specific dependencies
    "Flask-Markdown @git+https://git@github.com/psaiz/flask-markdown",
    "Flask-Mistune>=0.1.1",
    "mistune>=0.7.4",
    "pymdown-extensions>=5.0.0",
    "python-markdown-math>=0.3",
    "python-slugify>=1.2.4",
    # Webserver
    "uWSGI>=2.0.21",
    "uwsgitop>=0.11",
    # Pin Celery due to worker runtime issues
    "celery==5.2.7",
    # Pin XRootD consistently with Dockerfile
    "xrootd==5.8.3",
    "gevent==25.5.1",
    "greenlet>=3.2.2",
    "flask-babel==4.0.0",
    "raven<6.11",
    "dcxml",
    # And these ones are for the cold storage
    "fts3",
]

packages = find_packages()

setup(
    name="cernopendata",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    keywords="CERN Open Data",
    license="GPLv2",
    author="CERN",
    author_email="info@inveniosoftware.org",
    url="https://github.com/cernopendata/opendata.cern.ch",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "console_scripts": [
            "cernopendata = cernopendata.cli:cli",
        ],
        "invenio_assets.webpack": [
            "cernopendata_theme = cernopendata.modules.theme.webpack:theme",
            "cernopendata_glossary = cernopendata.modules.theme.webpack:glossary",
            "cernopendata_search = cernopendata.modules.theme.webpack:search_ui",
            "cernopendata_visualise = cernopendata.modules.theme.webpack:visualise",
            "cernopendata_records_file_box = "
            "cernopendata.modules.theme.webpack:records_file_box",
            "cernopendata_transfers = cernopendata.modules.theme.webpack:transfers",
        ],
        "invenio_base.apps": [
            "invenio_records_rest = invenio_records_rest:InvenioRecordsREST",
            "cernopendata_xrootd = cernopendata.modules.xrootd:CODPXRootD",
            "cernopendata_sitemap = cernopendata.modules.sitemap:CERNOpenDataSitemap",
            "cernopendata_globals = cernopendata.modules.globals.ext:GlobalVariables",
            "cernopendata_rq_wraps = cernopendata.modules.globals.ext:FlaskHeaders",
            # cod_md and cod_mistune are just wrappers to init the actual
            # markdown flask-extensions properly.
            "cod_md = " "cernopendata.modules.markdown.ext:CernopendataMarkdown",
            # 'cod_mistune = '
            # 'cernopendata.modules.mistune.ext:CernopendataMistune',
        ],
        "invenio_base.api_apps": [
            "cernopendata_xrootd = cernopendata.modules.xrootd:CODPXRootD",
            "cernopendata_rq_wraps = cernopendata.modules.globals.ext:FlaskHeaders",
        ],
        "invenio_base.api_blueprints": [
            "cernopendata_news_api = cernopendata.modules.api.news:blueprint",
        ],
        "invenio_base.blueprints": [
            "cernopendata = cernopendata.views:blueprint",
            "cernopendata_pages = " "cernopendata.modules.pages.views:blueprint",
            "cernopendata_theme = " "cernopendata.modules.theme.views:blueprint",
            "cernopendata_sitemap = " "cernopendata.modules.sitemap.views:blueprint",
        ],
        "invenio_config.module": [
            "cernopendata = cernopendata.config",
        ],
        "invenio_pidstore.minters": [
            "cernopendata_recid_minter = "
            " cernopendata.modules.records.minters.recid:"
            "cernopendata_recid_minter",
            "cernopendata_termid_minter = "
            " cernopendata.modules.records.minters.termid:"
            "cernopendata_termid_minter",
            "cernopendata_docid_minter = "
            " cernopendata.modules.records.minters.docid:"
            "cernopendata_docid_minter",
        ],
        "invenio_pidstore.fetchers": [
            "cernopendata_recid_fetcher = "
            " cernopendata.modules.records.fetchers.recid:"
            "cernopendata_recid_fetcher",
            "cernopendata_termid_fetcher = "
            " cernopendata.modules.records.fetchers.termid:"
            "cernopendata_termid_fetcher",
            "cernopendata_docid_fetcher = "
            " cernopendata.modules.records.fetchers.docid:"
            "cernopendata_docid_fetcher",
            "cernopendata_generic_fetcher = "
            " cernopendata.modules.records.fetchers.recid:"
            "cernopendata_generic_fetcher",
        ],
        "invenio_search.index_templates": [
            "records = cernopendata.modules.search.index_templates"
        ],
        "invenio_search.component_templates": [
            "records = cernopendata.modules.search.component_templates",
            "cold_storage = cernopendata.cold_storage.search.component_templates",
        ],
        "invenio_jsonschemas.schemas": [
            "cernopendata_schemas = cernopendata.jsonschemas",
        ],
        "flask.commands": [
            ## ALL OF THESE ONES ARE FOR THE COLD STORAGE. TAKE THEM TO A DEDICATED MODULE?
            "cold = cernopendata.cold_storage.cli:cold",
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
