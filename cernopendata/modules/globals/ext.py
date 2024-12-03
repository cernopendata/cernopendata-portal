"""Global variables for Flask app."""

import logging

from flask import Flask

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
        "lhcb": {"name": "LHCb", "url": "lhcb.web.cern.ch"},
        "opera": {"name": "OPERA", "url": "operaweb.lngs.infn.it"},
        "phenix": {
            "name": "PHENIX",
            "url": "www.phenix.bnl.gov",
            "height": 35,
            "width": "auto",
            "no_opendata_docs": True,
        },
        "totem": {"name": "TOTEM", "url": "totem-experiment.web.cern.ch"},
    }

    def __init__(self, app):
        """Extension initialization."""
        if not isinstance(app, Flask):
            return

        self.set_experiments(app)

    @staticmethod
    def set_experiments(app):
        """Sets the experiments to be displayed in templates.

        Use config `CERNOPENDATA_EXPERIMENTS` to exclude experiments.
        For the experiment_data the following fields are currently supported:
        name, url (of experiment), no_opendata_docs (exclude from about), height and width (image in footer)
        """
        experiment_data = GlobalVariables._experiments
        experiments = list(experiment_data.keys())

        # check config for custom setting
        if exclude_experiments := app.config.get("EXCLUDE_EXPERIMENTS"):
            try:
                exclude_experiments = [exp.lower() for exp in list(exclude_experiments)]
            except TypeError:
                logger.error(
                    f"Failed to exclude any experiments. Config EXCLUDE_EXPERIMENTS is not a list! "
                    f"Using default option..."
                )
            else:
                if set(experiments).issuperset(exclude_experiments):
                    logger.info(f"Loaded following experiments in view: {experiments}.")
                else:
                    invalid_choice = sorted(
                        set(exclude_experiments).difference(experiments)
                    )
                    logger.warning(
                        f"Loaded EXCLUDE_EXPERIMENTS with errors. Following are invalid: {invalid_choice}."
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
