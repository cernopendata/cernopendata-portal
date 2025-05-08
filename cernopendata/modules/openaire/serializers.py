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

from flask import request
from lxml import etree, html
from marshmallow import Schema, fields


def dict_to_lxml(d):
    """Convert a dictionary to an lxml element."""
    _ns = {
        "oaire": "http://namespace.openaire.eu/schema/oaire/",  # Default namespace (no prefix)
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
        "datacite": "http://datacite.org/schema/kernel-4",
    }

    _location = "http://namespace.openaire.eu/schema/oaire/ https://www.openaire.eu/schema/repo-lit/4.0/openaire.xsd"

    root = etree.Element("resource", nsmap=_ns, schema_location=_location)

    _nsmap = {
        # These are the attributes coming from datacite
        "identifier": "http://datacite.org/schema/kernel-4",
        "creators": "http://datacite.org/schema/kernel-4",
        "creator": "http://datacite.org/schema/kernel-4",
        "creatorName": "http://datacite.org/schema/kernel-4",
        "title": "http://datacite.org/schema/kernel-4",
        "titles": "http://datacite.org/schema/kernel-4",
        "dates": "http://datacite.org/schema/kernel-4",
        "date": "http://datacite.org/schema/kernel-4",
        "rights": "http://datacite.org/schema/kernel-4",
        # And these come from dc
        "publisher": "http://purl.org/dc/elements/1.1/",
        "description": "http://purl.org/dc/elements/1.1/",
        "resourceType": "http://namespace.openaire.eu/schema/oaire/",
    }

    def _build_etree(parent, d):
        """Recursively add elements to the parent element based on the dictionary."""
        if isinstance(d, dict):
            for key, value in d.items():
                if key.startswith("@"):  # Attribute handling
                    parent.set(key[1:], str(value))
                elif key == "#text":  # Text content handling
                    parent.text = str(value)
                else:  # Child elements
                    child = etree.SubElement(parent, f'{{{_nsmap.get(key, "")}}}{key}')
                    _build_etree(child, value)
        elif isinstance(d, list):
            for item in d:
                _build_etree(parent, item)
        else:
            parent.text = str(d)

    _build_etree(root, d)
    return root


def openaire_etree(pid, record):
    """Openaire XML format for OAI-PMH. It assumes that record is a search result."""
    data_dict = OpenAireSerializer().dump(record["_source"])
    return dict_to_lxml(data_dict)


class OpenAireSerializer(Schema):
    """DataCite complient schema."""

    identifier = fields.Method("get_identifier")
    creators = fields.Method("get_creator")
    titles = fields.Method("get_titles")
    resourceType = fields.Method("get_resourcetype")
    publisher = fields.Str()
    dates = fields.Method("get_publication_year")
    rights = fields.Method("get_rights")
    description = fields.Method("get_description")

    def get_publication_year(self, obj):
        """Get the publication date."""
        dates = []
        if "date_published" in obj:
            dates.append(
                {"date": {"@dateType": "Issued", "#text": obj["date_published"]}}
            )
        return dates

    def get_identifier(self, obj):
        """Get the identifier: DOI if it exists, URL if it does not."""
        if "doi" in obj:
            return {"@identifierType": "DOI", "#text": obj["doi"]}
        else:
            return {
                "@identifierType": "URL",
                "#text": f"https://{request.host}/record/{obj.get('recid')}",
            }

    def get_description(self, obj):
        """Get the description of the record."""
        descriptions = []
        if "abstract" in obj and "description" in obj["abstract"]:
            descriptions.append(
                {
                    "descriptionType": "abstract",
                    "description": html.fromstring(
                        obj["abstract"]["description"]
                    ).text_content(),
                }
            )
        return descriptions

    def get_rights(self, obj):
        """Get the access rights. Assume everything is open access."""
        return {
            "@rightsURI": "http://purl.org/coar/access_right/c_abf2",
            "#text": "open access",
        }

    def get_creator(self, obj):
        """Get creators based on authors or collaboration field."""
        authors = obj.get("authors", [obj.get("collaboration", None)])
        creators = []
        for author in authors:
            my_author = {"creator": {"creatorName": author["name"]}}
            if "orcid" in author:
                my_author["creator"]["nameIdentifiers"]: [
                    {
                        "nameIdentifier": author["orcid"],
                        "nameIdentifierScheme": "ORCID",
                        "schemeURI": "http://orcid.org/",
                    }
                ]
            creators.append(my_author)
        return creators

    def get_titles(self, obj):
        """Get title."""
        return [{"title": obj["title"]}]

    def get_resourcetype(self, obj):
        """Get resource type based on type field."""
        resource_type = "Other"
        uri = ""
        if obj["type"]:
            type_primary = obj["type"].get("primary", "")
            if type_primary == "Software":
                resource_type = "software"
                uri = "http://purl.org/coar/resource_type/c_5ce6"
            elif type_primary == "Dataset":
                resource_type = "dataset"
                uri = "http://purl.org/coar/resource_type/c_ddb1"
        return {
            "@resourceTypeGeneral": resource_type,
            "#text": resource_type,
            "@uri": uri,
        }
