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
        "titles": [record["_source"]["title"]],
        "creators": [record["_source"]["collaboration"]["name"]],
        "dates": [record["_source"]["date_published"]],
        "types": [record["_source"]["type"]["primary"]],
        "identifiers": [record["_source"]["pids"]["oai"]["id"]],
        "publishers": ["CERN Open Data"],
    }
    if "formats" in record["_source"]["distribution"]:
        data["formats"] = record["_source"]["distribution"]["formats"]
    if (
        "abstract" in record["_source"]
        and "description" in record["_source"]["abstract"]
    ):
        data["descriptions"] = [record["_source"]["abstract"]["description"]]

    return simpledc.dump_etree(data)
