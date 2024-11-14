"""Tests for the display experiment exclusion feature."""

import pytest
from bs4 import BeautifulSoup
from conftest import default_config

from cernopendata.factory import create_app
from cernopendata.modules.globals.ext import GlobalVariables
from cernopendata.modules.pages.views import index  # , faceted_search

ALL_EXPERIMENTS = sorted(GlobalVariables._experiments.keys())
EXCLUDE_ABOUT = sorted(
    [k for k, v in GlobalVariables._experiments.items() if v.get("no_opendata_docs")]
)


@pytest.fixture
def app_param(default_config):
    """Flask application fixture."""

    def _app_with_config(exclude=None):
        app = create_app(**default_config, EXCLUDE_EXPERIMENTS=exclude)

        with app.app_context():
            return app

    return _app_with_config


def get_experiments_from_about(page_soup):
    elements = page_soup.find_all("li", class_="ui dropdown")
    for element in elements:
        title = element.span.span.text

        if title.lower() == "about":
            not_experiment = ["cern open data", "glossary"]
            return [
                exp
                for div in element.div.find_all("div")
                if (exp := div.text.lower()) not in not_experiment
            ]


def get_experiments_from_site(page_soup):
    """Returns all experiments in lowercase from below the search bar."""
    elements = page_soup.find_all("div", class_="collections-col")
    for element in elements:
        title = element.header.span.text

        if title.lower() == "focus on":
            not_experiment = ["data science"]
            return [
                exp
                for li in element.ul.find_all("li")
                if (exp := li.text.lower()) not in not_experiment
            ]


def get_experiments_from_footer(page_soup):
    elements = page_soup.find("div", class_="logos")
    return [
        div.a.img.get("alt").rstrip(" experiment").lower()
        for div in elements.find_all("div")
    ]


def run_queries(flask_app):
    """Runs a query on the index page and returns the found experiments."""
    with flask_app.test_request_context("/"):
        soup = BeautifulSoup(index(), "html.parser")

        about = get_experiments_from_about(soup)
        body = get_experiments_from_site(soup)
        footer = get_experiments_from_footer(soup)

        return about, body, footer


# - Tests - - - - - - - - - -


def test_display_experiments_default(app_param):
    """Test default setting, focus on ordering and default functionality."""
    # setup
    flask_app = app_param()

    # query
    about, body, footer = run_queries(flask_app)

    # assert order
    assert sorted(about) == about
    assert sorted(body) == body
    assert sorted(footer) == footer

    # assert content
    assert sorted(about + EXCLUDE_ABOUT) == ALL_EXPERIMENTS
    assert body == ALL_EXPERIMENTS
    assert footer == ALL_EXPERIMENTS


def test_display_experiments_exclude_experiments(app_param):
    """Test different exclusions based on current setting."""
    # setup
    cases = [
        ["atlas", "totem"],
        ["alice", "lhcb"],
        ["opera"],
        ["delphi", "atlas", "phenix", "jade"],
    ]
    for case in cases:
        expected_result = [exp for exp in ALL_EXPERIMENTS if exp not in case]

        flask_app = app_param(exclude=case)

        # query
        about, body, footer = run_queries(flask_app)

        # assert content
        assert body == expected_result
        assert footer == expected_result
        assert set(about).difference(EXCLUDE_ABOUT) == set(expected_result).difference(
            EXCLUDE_ABOUT
        )


def test_display_experiments_invalid_parameter(app_param):
    """Test setting one of the experiments to an unknown value."""
    # setup
    case = ["error", "delphi"]
    expected_result = [exp for exp in ALL_EXPERIMENTS if exp not in case]

    flask_app = app_param(exclude=case)

    # query
    about, body, footer = run_queries(flask_app)

    # assert content
    assert body == expected_result
    assert footer == expected_result
    assert set(about).difference(EXCLUDE_ABOUT) == set(expected_result).difference(
        EXCLUDE_ABOUT
    )


def test_display_experiments_invalid_setting(app_param):
    """Test setting the configuration parameter to an invalid value."""
    # setup
    cases = ["i am not a valid setting", 0, True, {"key": "value"}]
    for case in cases:
        expected_result = ALL_EXPERIMENTS

        flask_app = app_param(exclude=case)

        # query
        about, body, footer = run_queries(flask_app)

        # assert content
        assert body == expected_result
        assert footer == expected_result
        assert set(about).difference(EXCLUDE_ABOUT) == set(expected_result).difference(
            EXCLUDE_ABOUT
        )


def test_display_experiments_empty_setting(app_param):
    """Test setting the configuration parameter to an empty value."""
    # setup
    case = []
    expected_result = ALL_EXPERIMENTS

    flask_app = app_param(exclude=case)

    # query
    about, body, footer = run_queries(flask_app)

    # assert content
    assert body == expected_result
    assert footer == expected_result
    assert set(about).difference(EXCLUDE_ABOUT) == set(expected_result).difference(
        EXCLUDE_ABOUT
    )


def test_display_experiments_exclude_all(app_param):
    """Tests if excluding all experiments works."""
    # setup
    case = ALL_EXPERIMENTS
    expected_result = []

    flask_app = app_param(exclude=case)

    # query
    about, body, footer = run_queries(flask_app)

    # assert content
    assert body == expected_result
    assert footer == expected_result
    assert set(about).difference(EXCLUDE_ABOUT) == set(expected_result).difference(
        EXCLUDE_ABOUT
    )


def test_display_experiments_exclude_glossary(app_param, monkeypatch):
    """Tests if excluding an experiment from the glossary works."""
    # setup
    experiments = {
        "atlas": {"name": "ATLAS", "no_opendata_docs": True},
        "cms": {"name": "CMS", "no_opendata_docs": True},
        "alice": {"name": "ALICE", "no_opendata_docs": False},
        "lhcb": {"name": "LHCb"},
    }
    monkeypatch.setattr(GlobalVariables, "_experiments", experiments)
    expected_result_glossary = ["alice", "lhcb"]
    expected_result_default = sorted(experiments.keys())

    flask_app = app_param()

    # query
    about, body, footer = run_queries(flask_app)

    # assert content
    assert body == expected_result_default
    assert footer == expected_result_default
    assert about == expected_result_glossary
