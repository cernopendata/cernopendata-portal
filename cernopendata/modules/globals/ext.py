import logging
from flask import Flask

from cernopendata.version import __version__

logger = logging.getLogger(__name__)


class GlobalVariables:
    """This class loads and holds global variables
    to be used in templates with context_processor."""

    def __init__(self, app):
        if not isinstance(app, Flask):
            return

        self.set_experiments(app)

    @staticmethod
    def set_experiments(app):
        """Sets the experiments to be displayed in templates
        available with env `CERNOPENDATA_EXPERIMENTS`"""

        experiment_data = {
            "alice": {"name": "ALICE", "url": "alice.cern", "width": 55, "height": 55},
            "atlas": {"name": "ATLAS", "url": "atlas.cern", "width": 55, "height": 55},
            "cms": {"name": "CMS", "url": "cms.cern", "width": 55, "height": 55},
            "delphi": {"name": "DELPHI", "img": "dolphin", "url": "delphi-www.web.cern.ch", "width": 55, "height": 55},
            "lhcb": {"name": "LHCb", "url": "https://www.phenix.bnl.gov", "width": 55, "height": 55},
            "opera": {"name": "OPERA", "url": "operaweb.lngs.infn.it", "width": 55, "height": 55},
            "phenix": {"name": "PHENIX", "url": "www.phenix.bnl.gov", "height": 35},
            "totem": {"name": "TOTEM", "url": "totem-experiment.web.cern.ch/", "height": 55},
        }
        experiments = experiment_data.keys()

        # check config for custom setting
        if custom_setting := app.config.get("INCLUDE_EXPERIMENTS"):
            try:
                custom_experiments = [exp.lower() for exp in list(custom_setting)]
            except TypeError:
                logger.error(f"Failed to load custom experiments. CERNOPENDATA_EXPERIMENTS is not a list! "
                             f"Using default.")
            else:
                if set(experiments).issuperset(custom_experiments):
                    experiments = custom_experiments
                    logger.info(f"Loaded following custom experiments in view: {experiments}")
                else:
                    invalid_experiments = sorted(set(custom_experiments).difference(experiments))
                    experiments = sorted(set(experiments).intersection(custom_experiments))
                    logger.warning(f"Loaded custom entries with errors. Following are invalid: {invalid_experiments}.")
        else:
            logger.info("Using default experiments in view.")

        # load settings as a "global" variable for templates
        experiments.sort()
        experiment_data = {k: v for k, v in experiment_data.items() if k in experiments}

        app.context_processor(lambda: {"experiments_display": experiment_data, "opendata_version": __version__})
