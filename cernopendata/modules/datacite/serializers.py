# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017 CERN.
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
"""Serializers for datacite module."""

from datacite import schema43
from flask import request
from lxml import etree
from marshmallow import Schema, fields

from bs4 import BeautifulSoup


def datacite_etree(pid, record):
    """Datacite XML format for OAI-PMH.

    It assumes that record is a search result.
    """
    # TODO: Ditto. See https://github.com/inveniosoftware/flask-resources/issues/117
    data_dict = DataCiteSerializer().dump(record["_source"])
    f = schema43.dump_etree(data_dict)

    if f.find("identifier") is None:
        identifier = etree.SubElement(f, "identifierType", identifierType="URL")
        identifier.text = (
            f"https://{request.host}/record/{record['_source'].get('recid')}"
        )
    return f


class DataCiteSerializer(Schema):
    """DataCite complient schema."""

    identifiers = fields.Method("get_identifiers")
    creators = fields.Method("get_creator")
    titles = fields.Method("get_titles")
    publisher = fields.Str()
    publicationYear = fields.Str(attribute="date_published")
    types = fields.Method("get_resourcetype")
    rightsList = fields.Method("get_rights")
    descriptions = fields.Method("get_description")
    language = fields.Method("get_language")
    subjects = fields.Method("get_subjects")

    def get_language(self, obj):
        """Get the language. Hardcoded to english."""
        return "en"

    def get_subjects(self, obj):
        """Get the keywords, based on the accelerator and experiment."""
        subjects = []
        for field in ["accelerator", "experiment"]:
            value = obj.get(field)
            if not value:
                continue

            if isinstance(value, str):
                values = [value]
            else:
                values = value  # assume list-like

            for v in values:
                if v:  # avoid empty strings / None
                    subjects.append({"subject": v})
        return subjects

    def get_description(self, obj):
        """Get the description of the object."""
        descriptions = []
        if obj.get("abstract") and obj.get("abstract").get("description"):
            descriptions.append(
                {
                    "descriptionType": "Abstract",
                    "description": obj.get("abstract").get("description"),
                }
            )
        if obj.get("methodology") and obj.get("methodology").get("description"):
            desc = BeautifulSoup(
                obj.get("methodology").get("description"), "html.parser"
            ).get_text()
            descriptions.append({"descriptionType": "Methods", "description": desc})

        usage = obj.get("usage", {}).get("description")
        if usage:
            usage = BeautifulSoup(usage, "html.parser").get_text()
            descriptions.append({"descriptionType": "Other", "description": usage})

        return descriptions

    def get_rights(self, obj):
        """Get the rights. Assume everything is open access."""
        return [{"rights": "open access"}]

    def get_identifiers(self, obj):
        """Get identifier based on doi field."""
        identifiers = []
        if obj.get("doi", ""):
            identifiers.append({"identifier": obj.get("doi"), "identifierType": "DOI"})
        return identifiers

    def get_creator(self, obj):
        """Get creators based on authors or collaboration field."""
        authors = obj.get("authors", [obj.get("collaboration", None)])
        creators = [
            {
                "name": author["name"],
                "nameIdentifiers": (
                    [
                        {
                            "nameIdentifier": author["orcid"],
                            "nameIdentifierScheme": "ORCID",
                            "schemeURI": "http://orcid.org/",
                        }
                    ]
                    if "orcid" in author
                    else []
                ),
            }
            for author in authors
        ]
        return creators

    def get_titles(self, obj):
        """Get title."""
        return [{"title": obj["title"]}]

    def get_resourcetype(self, obj):
        """Get resource type based on type field."""
        resource_type = "Other"
        if obj["type"]:
            type_primary = obj["type"].get("primary", "")
            if type_primary in ["Software", "Dataset"]:
                resource_type = type_primary
        return {
            "resourceTypeGeneral": resource_type,
            "resourceType": resource_type,
        }
