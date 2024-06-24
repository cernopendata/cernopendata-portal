from os import environ
from os.path import isfile

import pytest


def test_ispy():
    """Ensure that the module of ispy has been installed."""

    base_path = environ["INVENIO_INSTANCE_PATH"]
    assert isfile(f"{base_path}/static/node_modules/ispy-webgl/js/lib/Projector.js")
