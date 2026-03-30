# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2024 CERN.
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
"""Validation process."""
from .base import Validation
from .expected_fields import ExpectedFieldsValidation


class CMS_2016_Simulated(ExpectedFieldsValidation):
    """Check that the experiment is properly defined."""

    abstract = False

    name = "CMS 2016 Simulated"
    error_message = (
        "The records should follow the conventions of 2016 for simulated data."
    )
    experiment = "cms"
    optional = True

    def get_abstract(release, record):
        """Getting the title."""
        parts = [p for p in record["title"].split("/") if p]

        dataset = parts[0]
        data_format = parts[-1]
        return {
            "description": (
                f"<p>Simulated dataset {dataset} in {data_format} format for 2016 collision data.</p>"
                f"<p>See the description of the simulated dataset names in: "
                '<a href="/about/CMS-Simulated-Dataset-Names">About CMS simulated dataset names</a>.</p>'
                "<p>These simulated datasets correspond to the collision data collected by the CMS "
                "experiment in 2016.</p>"
            )
        }

    @staticmethod
    def get_record_type(record):
        """Get the type of record."""
        title = record.get("title", "")

        if "MINIAODSIM" in title:
            return "mini"
        elif "NANOAODSIM" in title:
            return "nano"
        return None

    def get_usage(release, record):
        """Get the usage for a particular record."""
        record_type = CMS_2016_Simulated.get_record_type(record)
        usage = {
            "mini": {
                "description": (
                    "You can access these data through the CMS Open Data container or the CMS Virtual "
                    "Machine. See the instructions for setting up one of the two alternative "
                    "environments and getting started in"
                ),
                "links": [
                    {
                        "description": "Running CMS analysis code using Docker",
                        "url": "/docs/cms-guide-docker#images",
                    },
                    {
                        "description": "How to install the CMS Virtual Machine",
                        "url": "/docs/cms-virtual-machine-cc7",
                    },
                    {
                        "description": "Getting started with CMS open data",
                        "url": "/docs/cms-getting-started-miniaod",
                    },
                ],
            },
            "nano": {
                "links": [
                    {
                        "url": "/docs/cms-guide-docker#nanoaod",
                        "description": "Using Docker containers",
                    },
                    {
                        "url": "/docs/cms-getting-started-nanoaod",
                        "description": "Getting started with CMS NanoAOD",
                    },
                ],
                "description": (
                    "You can access these data through XRootD protocol or direct download, "
                    "and they can be analysed with common ROOT and Python tools. See the instructions"
                    "for getting started in"
                ),
            },
        }
        return usage.get(record_type, None)

    def get_system_details(release, record):
        """Get the system details for a record."""
        record_type = CMS_2016_Simulated.get_record_type(record)
        usage = {
            "mini": {
                "container_images": [
                    {
                        "name": "docker.io/cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest",
                        "registry": "dockerhub",
                    },
                    {
                        "name": (
                            "gitlab-registry.cern.ch/cms-cloud/cmssw-docker-opendata/"
                            "cmssw_10_6_30-slc7_amd64_gcc700:latest"
                        ),
                        "registry": "gitlab",
                    },
                ],
                "global_tag": "106X_mcRun2_asymptotic_v17",
                "release": "CMSSW_10_6_30",
            },
            "nano": {
                "description": (
                    '<p>NANOAODSIM datasets are in the <a href="https://root.cern.ch/">ROOT</a>'
                    "tree format and their analysis does not require the use of CMSSW or CMS open"
                    "data environments. They can be analysed with common ROOT and Python tools.<p>"
                ),
                "container_images": [
                    {
                        "name": "gitlab-registry.cern.ch/cms-cloud/root-vnc",
                        "registry": "gitlab",
                    },
                    {
                        "name": "gitlab-registry.cern.ch/cms-cloud/python-vnc",
                        "registry": "gitlab",
                    },
                ],
            },
        }
        return usage.get(record_type, None)

    def parse_title(title):
        """Parse the title of a record, extracting the title and the type of record."""
        parts = [p for p in title.split("/") if p]

        dataset = parts[0] if len(parts) > 0 else None
        tier = parts[-1] if len(parts) > 0 else None

        return dataset, tier

    def get_relations(release, record):
        """Get the relations of a record."""
        title = record.get("title", "")
        dataset, tier = CMS_2016_Simulated.parse_title(title)

        if tier == "MINIAODSIM":
            target_tier = "NANOAODSIM"
            related = "NANO"
            rel_type = "isChildOf"

        elif tier == "NANOAODSIM":
            target_tier = "MINIAODSIM"
            related = "MINI"
            rel_type = "isParentOf"

        else:
            return None

        # 🔍 find matching record
        relation_record = next(
            (
                r
                for r in release.records
                if CMS_2016_Simulated.parse_title(r.get("title", ""))
                == (dataset, target_tier)
            ),
            None,
        )

        if relation_record is None:
            return f"IS THE TITLE {target_title} ?"
        return [
            {
                "description": f"The corresponding {related}AODSIM dataset:",
                "recid": relation_record["recid"],
                "type": rel_type,
            }
        ]

    def get_distribution_formats(release, record):
        """Get the distribution formats for a record."""
        record_type = CMS_2016_Simulated.get_record_type(record)
        return [f"{record_type}aodsim", "root"]

    def get_title_aditional(release, record):
        """Get the additional title for a record."""
        dataset, tier = CMS_2016_Simulated.parse_title(record.get("title"))
        return f"Simulated dataset {dataset} in {tier} format for 2016 collision data"

    expected_fields = {
        "abstract": get_abstract,
        "collections": ["CMS-Simulated-Datasets"],
        "collision_information": {"energy": "13TeV", "type": "pp"},
        "date_created": ["2016"],
        "distribution.formats": get_distribution_formats,
        "methodology.description": (
            "<p>These data were generated in several steps (see also "
            '<a href="/docs/cms-mc-production-overview">CMS Monte Carlo '
            "production overview</a>):</p>"
        ),
        "pileup": {
            "description": (
                "<p>To make these simulated data comparable with the collision data, "
                '<a href="/docs/cms-guide-pileup-simulation">pile-up events</a> are added to the'
                "simulated event in the DIGI2RAW step.</p>"
            ),
            "links": [
                {
                    "recid": "30595",
                    "title": "/Neutrino_E-10_gun/RunIISummer20ULPrePremix-UL16_106X_mcRun2_asymptotic_v13-v1/PREMIX",
                }
            ],
        },
        "run_period": ["Run2016G", "Run2016H"],
        "system_details": get_system_details,
        "type": {"primary": "Dataset", "secondary": ["Simulated"]},
        "relations": get_relations,
        "title_additional": get_title_aditional,
        "usage": get_usage,
        "validation": {
            "description": (
                "The generation and simulation of Monte Carlo data has been validated through general"
                "CMS validation procedures."
            )
        },
    }
