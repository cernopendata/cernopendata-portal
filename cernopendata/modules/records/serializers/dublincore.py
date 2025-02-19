"""Dublin Core dumper."""

from dcxml import simpledc


def dumps_etree(pid, record, **kwargs):
    """Dumps the record object with the fields defined by the Simlpe Dublin Core.

    :param pid: pid of the record
    :param record: json format of the record
    :param kwargs: None
    :return:
    """
    data = {
        "titles": [record["_source"].get("title", None)],
        "creators": [record["_source"].get("collaboration", {}).get("name", None)],
        "dates": [record["_source"].get("date_published", None)],
        "types": [record["_source"].get("type", {}).get("primary", None)],
        "identifiers": [
            record["_source"].get("pids", {}).get("oai", {}).get("id", None)
        ],
        "publishers": ["CERN Open Data"],
    }
    if record["_source"].get("distribution", {}).get("formats", None):
        data["formats"] = record["_source"]["distribution"]["formats"]
    if record["_source"].get("abstract", {}).get("description", None):
        data["descriptions"] = [record["_source"]["abstract"]["description"]]

    return simpledc.dump_etree(data)
