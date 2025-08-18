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

import logging
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
from .storage import Storage

logger = logging.getLogger(__name__)

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
option_ignore_tag = click.option(
    "--force",
    is_flag=True,
    help="Force the deletion even if hot_deleted tag already exists",
)
option_limit = click.option(
    "--limit",
    default=False,
    type=click.INT,
    help="Specify how many files should be affected. The limit can be a positive or a negative. "
    + "In case of negative numbers, it leaves those many files without issuing transfers",
)

option_verify = click.option(
    "-v", "--verify", is_flag=True, help="Verifies that all the files listed exist"
)

option_debug = click.option(
    "-d", "--debug", is_flag=True, help="Swicth on the debug messages"
)

option_max_transfers = click.option(
    "-m",
    "--max_transfers",
    type=click.INT,
    help="Maximum number of transfers that could be issued.",
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
@option_debug
@option_max_transfers
def archive(record, register, limit, force, dry, debug, max_transfers):
    """Move a record to cold."""
    _doOperation(
        ColdStorageActions.ARCHIVE,
        record,
        register,
        limit,
        force,
        dry,
        debug,
        max_transfers,
    )


def _doOperation(
    operation, record, register, limit, force, dry, debug, max_transfers=0
):
    """Internal function to do the CLI commands."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    m = ColdStorageManager()
    counter = 0
    transfers = 0
    for r in record:
        try:
            uuid = PersistentIdentifier.get("recid", r).object_uuid
        except PIDDoesNotExistError as e:
            click.secho(f"The entry {r} does not exist", fg="red")
            continue
        t = m.doOperation(operation, uuid, limit, register, force, dry, max_transfers)
        if operation == ColdStorageActions.CLEAR_HOT and not t:
            click.secho(f"Unable to complete operation for record {r}", fg="red")
            continue
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
@option_debug
@option_max_transfers
def stage(record, register, limit, force, dry, debug, max_transfers):
    """Move a record from cold."""
    _doOperation(
        ColdStorageActions.STAGE,
        record,
        register,
        limit,
        force,
        dry,
        debug,
        max_transfers,
    )


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
@option_verify
@option_debug
def list(record, verify, debug):
    """Print the urls for an entry.

    By default, it prints the urls for all the files of the entry.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
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
            if "hot_deleted" not in f.get("tags", {}):
                print(f"    * Hot copy: {f['uri']}")
                stats["hot"] += 1
                stats["size_hot"] += f["size"]
            if "uri_cold" in f.get("tags", {}):
                print(f"    * Cold copy: {f['tags']['uri_cold']}")
                stats["cold"] += 1
                stats["size_cold"] += f["size"]
            if verify:
                stats["errors"] += _verify_files(f)

    click.secho(
        f"Summary: {stats['files']} files ({file_size(stats['size'])}), with {stats['hot']} hot copies"
        + f" ({file_size(stats['size_hot'])}) and {stats['cold']} cold copies ({file_size(stats['size_cold'])}) ",
        fg="green",
    )
    if stats["errors"]:
        click.secho(f"The following records have issues: {stats['errors']}", fg="red")
        raise click.exceptions.Exit(1)


def _verify_files_exists(uri: str, exists: bool, should_exist: bool) -> str:
    """Check the consistency between the repo and storage for a given uri."""
    error = []
    if should_exist and not exists:
        error = f"The file '{uri}' does not exist"
    if exists and not should_exist:
        error = f"The file '{uri}' exists but it is not registered"
    if error:
        click.secho(f"{error}", fg="red")
    return error


def _verify_files(file: dict) -> list:
    """Verify that the files registered in the repository exists.

    It also checks if there are similar files
    that exist in the storage and are not registered
    """
    errors = []
    hot_copy, _ = Storage.verify_file(file["uri"], file["size"], file["checksum"])
    new_error = _verify_files_exists(
        file["uri"], hot_copy, "hot_deleted" not in file.get("tags", {})
    )
    if new_error:
        errors.append(new_error)

    if "tags" in file and "uri_cold" in file["tags"]:
        cold_uri = file["tags"]["uri_cold"]
    else:
        cold_uri, _ = Storage.find_url(ColdStorageActions.ARCHIVE, file["uri"])
    cold_copy, _ = Storage.verify_file(cold_uri, file["size"], file["checksum"])
    new_error = _verify_files_exists(
        cold_uri, cold_copy, "uri_cold" in file.get("tags", {})
    )
    if new_error:
        errors.append(new_error)
    return errors


@cold.command()
@with_appcontext
@argument_record
@option_limit
@option_ignore_tag
@option_dry
@option_debug
def clear_hot(record, limit, force, dry, debug):
    """Delete the hot copy of a file that has a cold copy."""
    _doOperation(ColdStorageActions.CLEAR_HOT, record, None, limit, force, dry, debug)


@cold.command()
@with_appcontext
@option_debug
def process_transfers(debug):
    """Check the status of the transfers."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    return TransferService.process_transfers()


@cold.command()
@with_appcontext
@option_debug
def process_requests(debug):
    """Check the status of the requests."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    return RequestService.process_requests()
