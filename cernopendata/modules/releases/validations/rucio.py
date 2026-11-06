"""Validation process."""

import os
from datetime import datetime

from rucio.client.didclient import DIDClient

from .base import Validation


class RucioDatasets(Validation):
    """Validation to translate datasets into filenames."""

    name = "Rucio datasets"
    error_message = "There are some rucio datasets that have not been expanded."
    experiment = {"cms", "atlas"}
    optional = True

    def _get_paths(self, experiment):
        """Return the Rucio config dir and X509 proxy path for an experiment."""
        home = os.environ["HOME"]
        rucio_home = os.path.join(home, experiment, "rucio")
        user_proxy = os.path.join(home, ".globus", experiment, "userproxy.pem")
        return rucio_home, user_proxy

    def _get_config_errors(self, experiment):
        """Return errors if the Rucio config or X509 proxy are missing."""
        rucio_home, user_proxy = self._get_paths(experiment)
        errors = []
        if not os.path.isdir(rucio_home):
            errors.append(
                f"Missing Rucio configuration for {experiment} (expected {rucio_home})"
            )
        if not os.path.isfile(user_proxy):
            errors.append(
                f"Missing X509 proxy for {experiment} (expected {user_proxy})"
            )
        return errors

    def _setup_environment(self, experiment):
        """Point the Rucio client at the experiment's config and proxy."""
        rucio_home, user_proxy = self._get_paths(experiment)
        os.environ["RUCIO_HOME"] = rucio_home
        os.environ["X509_USER_PROXY"] = user_proxy

    def fixable(self, release=None):
        """Only offer the automatic fix when the Rucio environment is set up."""
        return not self._get_config_errors(release.experiment)

    def validate(self, release):
        """Check if there are any entries with rucio_dataset and no files."""
        errors = self._get_config_errors(release.experiment)
        if errors:
            return errors
        for i, record in enumerate(release.records):
            if "rucio_dataset" in record and "files" not in record:
                errors.append(f"The record {i + 1} has a rucio rule and no files")
        return errors

    def _get_files_from_rucio_dataset(self, rucio_client, did, experiment):
        result = []
        scope, name = did.split(":", 1)

        files = list(rucio_client.list_files(scope, name))
        for f in files:
            result.append(
                {
                    "checksum": f"adler32:{f.get('adler32')}",
                    "key": os.path.basename(f["name"]),
                    "size": f.get("bytes"),
                    "uri": f"root://eospublic.cern.ch//eos/opendata/{experiment}/{f['name']}",
                }
            )
        return result

    def fix(self, release):
        """Fix the entries that have rucio_dataset and no files."""
        experiment = release.experiment
        errors = self._get_config_errors(experiment)
        if errors:
            return errors
        self._setup_environment(experiment)
        rucio_client = DIDClient()
        for record in release.records:
            if "rucio_dataset" in record and "files" not in record:
                files = self._get_files_from_rucio_dataset(
                    rucio_client, record["rucio_dataset"], experiment
                )
                record["title"] = record["rucio_dataset"].split(":", 1)[1]
                record["files"] = files
                record["date_published"] = str(datetime.now().year)
                record["distribution"] = {
                    "formats": ["nanoaodsim", "root"],
                    "number_files": len(files),
                }
                record["type"] = {"primary": "Dataset"}
        return errors
