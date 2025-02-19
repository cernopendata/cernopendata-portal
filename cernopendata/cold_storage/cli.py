# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017-2025 CERN.
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

"""Cold Storage CLI."""

import json
import sys
from functools import wraps
from math import log2

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError

from .manager import ColdStorageManager

argument_record = click.argument("record", nargs=-1, required=True, metavar="RECORD")

# option_file = click.option(
#    "-f", "--file", multiple=True, default=[], metavar="FILE", help="File(s)."
# )

option_register = click.option(
    "--register/--no-register",
    help="If the file already exists at the destination,  "
    + "with the same file and checksum, import it without issuing the transfer",
)
option_dry = click.option("--dry/--do-it", default=False, help="Do not issue transfers")
option_debug = click.option("--debug/--no-debug", default=False)
option_exists = click.option("--check-exists/--no-check-exists", default=True)

option_limit = click.option(
    "--limit",
    default=False,
    type=click.INT,
    help="Specify how many files should be affected. The limit can be a positive or a negative. "
    + "In case of negative numbers, it leaves those many files without issuing transfers",
)


# From https://stackoverflow.com/questions/1094841/get-a-human-readable-version-of-a-file-size
def file_size(size):
    """Convert a size in bytes to a human readable format."""
    _suffixes = ["bytes", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    order = int(log2(size) / 10) if size else 0
    return "{:.4g} {}".format(size / (1 << (order * 10)), _suffixes[order])


@click.group()
def cold():
    """Manage the cold interface."""


@cold.command()
@with_appcontext
@argument_record
@option_register
@option_debug
@option_limit
@option_exists
@option_dry
def archive(record, register, debug, limit, check_exists, dry):
    """Move a record to cold."""
    _doOperation("archive", record, register, debug, limit, check_exists, dry)


def _doOperation(operation, record, register, debug, limit, check_exists, dry):
    """Internal function to do the CLI commands."""
    m = ColdStorageManager(current_app, debug)
    counter = 0
    transfers = 0
    for r in record:
        try:
            uuid = PersistentIdentifier.get("recid", r).object_uuid
        except PIDDoesNotExistError as e:
            click.secho(f"The entry {r} does not exist", fg="red")
            continue
        t = m.doOperation(operation, uuid, limit, register, check_exists, dry)
        transfers += len(t)
        counter += 1
        click.secho(
            f"Record {r} done. Entry {counter} out of {len(record)} done. {transfers} issued so far",
            fg="green",
        )


@cold.command()
@with_appcontext
@argument_record
@option_register
@option_debug
@option_limit
@option_exists
@option_dry
def stage(record, register, debug, limit, check_exists, dry):
    """Move a record from cold."""
    _doOperation("stage", record, register, debug, limit, check_exists, dry)


@cold.command()
@with_appcontext
def settings():
    """Display the list of configured cold endpoints."""
    m = ColdStorageManager(current_app)
    click.secho(f"The cold storage interface will store in: {m.settings()}")


@cold.command()
@with_appcontext
@argument_record
@option_debug
def list(record, debug):
    """Print the urls for an entry.

    By default, it prints the urls for all the files of the entry.
    """
    m = ColdStorageManager(current_app, debug)
    stats = {
        "files": 0,
        "hot": 0,
        "cold": 0,
        "size": 0,
        "size_hot": 0,
        "size_cold": 0,
        "errors": [],
    }
    for r in record:
        try:
            uuid = PersistentIdentifier.get("recid", r).object_uuid
        except Exception as e:
            click.secho(f"The record '{r}' does not exist.", fg="red")
            continue
        info = m.list(uuid)
        if debug:
            print("Printing debug info", info)
        if not info:
            click.secho(f"The record {r} does not exist!")
            stats["errors"] += [r]
            continue
        click.secho(f"The files referenced in '{r}' are:", fg="green")

        for f in info:
            stats["files"] += 1
            stats["size"] += f["size"]
            if "tags" not in f or "hot_deleted" not in f["tags"]:
                print(f"    * Hot copy: {f['uri']}")
                stats["hot"] += 1
                stats["size_hot"] += f["size"]
            if "tags" in f and "uri_cold" in f["tags"]:
                print(f"    * Cold copy: {f['tags']['uri_cold']}")
                stats["cold"] += 1
                stats["size_cold"] += f["size"]

    click.secho(
        f"Summary: {stats['files']} files ({file_size(stats['size'])}), with {stats['hot']} hot copies"
        + f" ({file_size(stats['size_hot'])}) and {stats['cold']} cold copies ({file_size(stats['size_cold'])}) ",
        fg="green",
    )
    if stats["errors"]:
        click.secho(f"The following records have issues: {stats['errors']}", fg="red")
        return -1


@cold.command()
@with_appcontext
@argument_record
@option_limit
@option_dry
@option_debug
def clear_hot(record, limit, dry, debug):
    """Delete the hot copy of a file that has a cold copy."""
    _doOperation("clear_hot", record, None, debug, limit, None, dry)


@cold.command()
@with_appcontext
@option_debug
def check_transfers(debug):
    """Check the status of the transfers."""
    m = ColdStorageManager(current_app, debug)
    return m.check_current_transfers()


@cold.command()
@with_appcontext
@option_debug
def check_requests(debug):
    """Check the status of the requests."""
    m = ColdStorageManager(current_app, debug)
    return m.check_requests()
