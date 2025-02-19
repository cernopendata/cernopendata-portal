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

from math import log2

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier

from .api import ColdStorageActions
from .manager import ColdStorageManager
from .models import Location
from .service import RequestService, TransferService

argument_record = click.argument("record", nargs=-1, required=True, metavar="RECORD")


option_register = click.option(
    "--register/--no-register",
    help="If the file already exists at the destination,  "
    + "with the same file and checksum, import it without issuing the transfer",
)
option_dry = click.option("--dry/--do-it", default=False, help="Do not issue transfers")
option_force = click.option(
    "--force/--no-force",
    default=False,
    help="Force the transfer, without checking if the file exists",
)

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
@option_limit
@option_force
@option_dry
def archive(record, register, limit, force, dry):
    """Move a record to cold."""
    _doOperation(ColdStorageActions.ARCHIVE, record, register, limit, force, dry)


def _doOperation(operation, record, register, limit, force, dry):
    """Internal function to do the CLI commands."""
    m = ColdStorageManager()
    counter = 0
    transfers = 0
    for r in record:
        try:
            uuid = PersistentIdentifier.get("recid", r).object_uuid
        except PIDDoesNotExistError as e:
            click.secho(f"The entry {r} does not exist", fg="red")
            continue
        t = m.doOperation(operation, uuid, limit, register, force, dry)
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
@option_limit
@option_force
@option_dry
def stage(record, register, limit, force, dry):
    """Move a record from cold."""
    _doOperation(ColdStorageActions.STAGE, record, register, limit, force, dry)


@cold.group()
@with_appcontext
def location():
    """Manages locations."""
    pass


@location.command()
@click.option("--cold-path", required=True, help="Path to cold storage.")
@click.option("--hot-path", required=True, help="Path to hot storage.")
@click.option("--manager-class", required=True, help="The manager class name.")
@with_appcontext
def add(cold_path, hot_path, manager_class):
    """Add a location."""
    loc = Location(cold_path=cold_path, hot_path=hot_path, manager_class=manager_class)
    db.session.add(loc)
    db.session.commit()
    click.echo(f"Location added with ID {loc.id}")


@location.command()
def list():
    """List locations."""
    locations = Location.query.all()
    if not locations:
        click.echo("No locations found.")
    else:
        for loc in locations:
            click.echo(
                f"ID: {loc.id}, Cold Path: {loc.cold_path}, Hot Path: {loc.hot_path}, Manager: {loc.manager_class}"
            )


@cold.command()
@with_appcontext
@argument_record
def list(record):
    """Print the urls for an entry.

    By default, it prints the urls for all the files of the entry.
    """
    m = ColdStorageManager()
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
def clear_hot(record, limit, dry):
    """Delete the hot copy of a file that has a cold copy."""
    _doOperation(ColdStorageActions.CLEAR_HOT, record, None, limit, None, dry)


@cold.command()
@with_appcontext
def process_transfers():
    """Check the status of the transfers."""
    return TransferService.process_transfers()


@cold.command()
@with_appcontext
def process_requests():
    """Check the status of the requests."""
    return RequestService.process_requests()
