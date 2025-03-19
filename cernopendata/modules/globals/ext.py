"""Global variables and methods for Flask app."""

import logging
import json
import os

from flask import Flask, request
from counter_robots import is_robot_or_machine

from cernopendata.version import __version__

logger = logging.getLogger(__name__)


class GlobalVariables:
    """Global variables Invenio module.

    This class loads and holds global variables
    to be used in templates with context_processor.

    For the `_experiments` the following fields are currently supported:
    - name (of the experiment)
    - url (of the experiment)
    - no_opendata_docs (exclude mention from about page)
    - height and width (image in footer)
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

        Use environment variable `CERNOPENDATA_EXCLUDE_EXPERIMENTS` to exclude experiments.
        Pass a JSON valid list of experiment names to exclude them.
        """
        experiment_data = GlobalVariables._experiments
        experiments = list(experiment_data.keys())

        # check config for custom setting
        if exclude_experiments := os.getenv("CERNOPENDATA_EXCLUDE_EXPERIMENTS"):
            try:
                excl_list = json.loads(exclude_experiments.replace("'", '"'))

                if not all([isinstance(exp, str) for exp in excl_list]):
                    raise json.JSONDecodeError(
                        "CERNOPENDATA_EXCLUDE_EXPERIMENTS is not an iterable yielding strings!",
                        *("", 0),
                    )

                logger.info("Loaded experiments from CERNOPENDATA_EXCLUDE_EXPERIMENTS")

            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to exclude experiments from view. "
                    "Config CERNOPENDATA_EXCLUDE_EXPERIMENTS is not a json list!"
                )
                raise e

            exclude_experiments = [exp.lower() for exp in list(excl_list)]

            if set(experiments).issuperset(exclude_experiments):
                logger.info("Loading following experiments in view: %s.", experiments)
            else:
                invalid_choice = sorted(
                    set(exclude_experiments).difference(experiments)
                )
                logger.warning(
                    "Loaded CERNOPENDATA_EXCLUDE_EXPERIMENTS with errors. "
                    "Following are invalid: %s.",
                    invalid_choice,
                )

            experiments = list(set(experiments).difference(exclude_experiments))

        else:
            logger.info(
                "CERNOPENDATA_EXCLUDE_EXPERIMENTS not set. Using default experiments in view."
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
