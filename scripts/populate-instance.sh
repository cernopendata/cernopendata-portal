#!/usr/bin/env bash
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017, 2018, 2022 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

set -o errexit
set -o nounset

cernopendata db init
cernopendata db create
cernopendata index init
sleep 20

cernopendata files location local var/data --default
cernopendata cold location add --cold-path https://eosctapublic.cern.ch:8444/eos/ctapublic/archive/opendata/ --hot-path root://eospublic.cern.ch//eos/opendata/ --manager-class cernopendata.cold_storage.transfer.fts.TransferManager

if [[ "$@" = *"--skip-glossary"* ]]; then
    echo "[INFO] Skipping loading of glossary terms."
else
    cernopendata fixtures glossary --mode insert
fi

if [[ "$@" = *"--skip-docs"* ]]; then
    echo "[INFO] Skipping loading of docs."
else
    cernopendata fixtures docs --mode insert
fi

cernopendata shell scripts/create_oaisets.py

echo "The instance has been populated successfully :-)"