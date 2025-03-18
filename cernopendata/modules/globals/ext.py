"""Global variables and methods for Flask app."""

import logging
import json

from flask import Flask, request
from counter_robots import is_robot_or_machine

from cernopendata.version import __version__

logger = logging.getLogger(__name__)


class GlobalVariables:
    """Global variables Invenio module.

    This class loads and holds global variables
    to be used in templates with context_processor.
    """

    _experiments = {
        "alice": {"name": "ALICE", "url": "alice.cern"},
        "atlas": {"name": "ATLAS", "url": "atlas.cern"},
        "cms": {"name": "CMS", "url": "cms.cern"},
        "delphi": {"name": "DELPHI", "url": "delphi-www.web.cern.ch"},
        "jade": {"name": "JADE", "url": "wwwjade.mpp.mpg.de"},
        "lhcb": {"name": "LHCb", "url": "lhcb.web.cern.ch"},
        "opera": {"name": "OPERA", "url": "en.wikipedia.org/wiki/OPERA_experiment"},
        "phenix": {
            "name": "PHENIX",
            "url": "www.phenix.bnl.gov",
            "height": 35,
            "width": "auto",
            "no_opendata_docs": True,
        },
        "totem": {
            "name": "TOTEM",
            "url": "totem-experiment.web.cern.ch",
            "width": "auto",
        },
    }

    def __init__(self, app):
        """Extension initialization."""
        if not isinstance(app, Flask):
            return

        self.set_experiments(app)

    @staticmethod
    def set_experiments(app):
        """Sets the experiments to be displayed in templates.

        Use environment variable `EXCLUDE_EXPERIMENTS` to exclude experiments.
        Pass a JSON valid list of experiments to exclude them.

        For the `experiment_data` the following fields are currently supported:
        name, url (of experiment), no_opendata_docs (exclude from about page), height and width
        (image in footer).
        """
        experiment_data = GlobalVariables._experiments
        experiments = list(experiment_data.keys())

        # check config for custom setting
        if exclude_experiments := app.config.get("EXCLUDE_EXPERIMENTS"):
            try:
                exclude_experiments = json.loads(
                    str(exclude_experiments).replace("'", '"')
                )
                logger.info("Loaded experiments from EXCLUDE_EXPERIMENTS")

            except json.JSONDecodeError:
                logger.error(
                    "Failed to exclude experiments from view. "
                    "Config EXCLUDE_EXPERIMENTS is not a json list! "
                    "Using default..."
                )
                exclude_experiments = []

            exclude_experiments = [exp.lower() for exp in list(exclude_experiments)]

            if set(experiments).issuperset(exclude_experiments):
                logger.info("Loading following experiments in view: %s.", experiments)
            else:
                invalid_choice = sorted(
                    set(exclude_experiments).difference(experiments)
                )
                logger.warning(
                    "Loaded EXCLUDE_EXPERIMENTS with errors. Following are invalid: %s.",
                    invalid_choice,
                )

            experiments = list(set(experiments).difference(exclude_experiments))

        else:
            logger.info(
                "EXCLUDE_EXPERIMENTS not set. Using default experiments in view."
            )

        # load settings as a "global" variable for templates
        experiment_data = {
            k: experiment_data[k]
            for k in sorted(experiment_data.keys())
            if k in experiments
        }

        app.context_processor(
            lambda: {
                "experiments_display": experiment_data,
                "opendata_version": __version__,
            }
        )


class FlaskHeaders:
    """This class sets headers for the Flask app."""

    def __init__(self, app):
        """Extension initialization."""
        if not isinstance(app, Flask):
            return

        @app.after_request
        def add_requestor_header(response):
            try:
                agent = request.user_agent.string

                if is_robot_or_machine(agent):
                    response.headers["X-User-Category"] = "robot"
                else:
                    response.headers["X-User-Category"] = "user"

            finally:
                return response
