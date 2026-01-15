import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from cernopendata.modules.releases.api import Release
from cernopendata.modules.releases.models import ReleaseStatus


def test_list_releases(client):
    # Patch current_user to be authenticated
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    with patch("cernopendata.modules.releases.views.current_user", mock_user), patch(
        "cernopendata.modules.releases.views.Release.validate_experiment",
        return_value=True,
    ), patch(
        "cernopendata.modules.releases.views.curator_experiments",
        return_value={"curator_experiments": ["cms"]},
    ), patch(
        "cernopendata.modules.releases.views.Release.list_releases", return_value=[]
    ):

        res = client.get("/releases/api/list/cms")  # no follow_redirects!


#       assert res.status_code == 200
