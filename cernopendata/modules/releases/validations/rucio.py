"""Validation process."""

import os

from rucio.client.didclient import DIDClient

from .base import Validation


class RucioDatasets(Validation):
    """Validation to translate datasets into filenames."""

    name = "Rucio datasets"
    error_message = "There are some rucio datasets that have not been expanded"
    experiment = "cms"
    optional = True

    def validate(self, release):
        """Check if there are any entries with rucio_dataset and no files."""
        errors = []
        for i, record in enumerate(release.records):
            if "rucio_dataset" in record and "files" not in record:
                errors.append(f"The record {i} has a rucio rule and no files")
        return errors

    def _get_files_from_rucio_dataset(self, rucio_client, did):
        result = []
        scope, name = did.split(":", 1)

        try:
            files = list(rucio_client.list_files(scope, name))
            if files:
                for f in files:
                    result.append(
                        {
                            "checksum": f"adler32:{f.get('adler32')}",
                            "key": os.path.basename(f["name"]),
                            "size": f.get("bytes"),
                            "uri": f"root://eospublic.cern.ch//eos/opendata/cms/{f['name']}",
                        }
                    )
                return
        except Exception:
            pass

        return result

    def fix(self, release):
        """Fix the entries that have rucio_dataset and no files."""
        os.environ["RUCIO_HOME"] = f"{os.environ['HOME']}/rucio"
        os.environ["X509_USER_PROXY"] = f"{os.environ['HOME']}/.globus/userproxy.pem"
        errors = []
        rucio_client = DIDClient()
        for i, record in enumerate(release.records):
            if "rucio_dataset" in record and "files" not in record:
                (schema, dataset_type, dataset_date, dataset_format) = record[
                    "rucio_dataset"
                ].split("/")
                files = self.get_files_from_rucio_dataset(
                    rucio_client, record["rucio_dataset"]
                )
                record["title"] = record["rucio_dataset"][4:]
                record["title_additional"] = (
                    f"Simulated dataset {dataset_type} in {dataset_format} format for 2017 collision data"
                )
                record["files"] = files
                record["date_published"] = "2026"
                record["distribution"] = {
                    "formats": ["nanoaodsim", "root"],
                    "number_files": len(files),
                }
                record["type"] = {"primary": "Dataset", "secondary": ["Simulated"]}
        return errors
