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
        "descriptions": [record["_source"]["abstract"]["description"]],
        "dates": [record["_source"]["date_published"]],
        "types": [record["_source"]["type"]["primary"]],
        "formats": record["_source"]["distribution"]["formats"],
        "identifiers": [record["_source"]["pids"]["oai"]["id"]],
        "publishers": ["CERN OPEN DATA"],
    }

    return simpledc.dump_etree(data)
