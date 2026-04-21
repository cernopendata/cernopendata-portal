import pytest

from cernopendata.modules.releases.validations.cms_2016 import CMS_2016_Simulated


class DummyRelease:
    def __init__(self, records):
        self.records = records


# -------------------------
# get_record_type
# -------------------------
def test_get_record_type_mini():
    record = {"title": "/A/B/MINIAODSIM"}
    assert CMS_2016_Simulated().get_record_type(record) == "mini"


def test_get_record_type_nano():
    record = {"title": "/A/B/NANOAODSIM"}
    assert CMS_2016_Simulated().get_record_type(record) == "nano"


def test_get_record_type_none():
    record = {"title": "/A/B/OTHER"}
    assert CMS_2016_Simulated().get_record_type(record) is None


# -------------------------
# parse_title
# -------------------------
def test_parse_title_normal():
    dataset, tier = CMS_2016_Simulated().parse_title("/A/B/MINIAODSIM")
    assert dataset == "A"
    assert tier == "MINIAODSIM"


def test_parse_title_empty():
    dataset, tier = CMS_2016_Simulated().parse_title("")
    assert dataset is None
    assert tier is None


# -------------------------
# get_usage
# -------------------------
def test_get_usage_mini():
    record = {"title": "/A/B/MINIAODSIM"}
    usage = CMS_2016_Simulated().get_usage(None, record)

    assert usage is not None
    assert "description" in usage
    assert len(usage["links"]) == 3


def test_get_usage_nano():
    record = {"title": "/A/B/NANOAODSIM"}
    usage = CMS_2016_Simulated().get_usage(None, record)

    assert usage is not None
    assert "description" in usage
    assert len(usage["links"]) == 2


def test_get_usage_none():
    record = {"title": "/A/B/OTHER"}
    usage = CMS_2016_Simulated().get_usage(None, record)

    assert usage is None


# -------------------------
# get_system_details
# -------------------------
def test_get_system_details_mini():
    record = {"title": "/A/B/MINIAODSIM"}
    details = CMS_2016_Simulated().get_system_details(None, record)

    assert details["release"] == "CMSSW_10_6_30"
    assert "container_images" in details


def test_get_system_details_nano():
    record = {"title": "/A/B/NANOAODSIM"}
    details = CMS_2016_Simulated().get_system_details(None, record)

    assert "description" in details
    assert len(details["container_images"]) == 2


def test_get_system_details_none():
    record = {"title": "/A/B/OTHER"}
    details = CMS_2016_Simulated().get_system_details(None, record)

    assert details is None


# -------------------------
# get_relations
# -------------------------
def test_get_relations_mini_to_nano():
    record = {"title": "/DATASET/X/MINIAODSIM", "recid": "1"}
    related = {"title": "/DATASET/X/NANOAODSIM", "recid": "2"}

    release = DummyRelease(records=[record, related])

    relations = CMS_2016_Simulated().get_relations(release, record)

    assert relations[0]["recid"] == "2"
    assert relations[0]["type"] == "isChildOf"


def test_get_relations_nano_to_mini():
    record = {"title": "/DATASET/X/NANOAODSIM", "recid": "2"}
    related = {"title": "/DATASET/X/MINIAODSIM", "recid": "1"}

    release = DummyRelease(records=[record, related])

    relations = CMS_2016_Simulated().get_relations(release, record)

    assert relations[0]["recid"] == "1"
    assert relations[0]["type"] == "isParentOf"


def test_get_relations_no_match():
    record = {"title": "/DATASET/X/MINIAODSIM", "recid": "1"}
    release = DummyRelease(records=[record])

    result = CMS_2016_Simulated().get_relations(release, record)

    assert result is None


def test_get_relations_invalid_tier():
    record = {"title": "/DATASET/X/OTHER"}
    release = DummyRelease(records=[record])

    assert CMS_2016_Simulated().get_relations(release, record) is None


# -------------------------
# get_distribution_formats
# -------------------------
def test_distribution_formats():
    record = {"title": "/A/B/MINIAODSIM"}
    formats = CMS_2016_Simulated().get_distribution_formats(None, record)

    assert formats == ["miniaodsim", "root"]


# -------------------------
# get_title_additional
# -------------------------
def test_title_additional():
    record = {"title": "/DATASET/X/MINIAODSIM"}
    title = CMS_2016_Simulated().get_title_aditional(None, record)

    assert "DATASET" in title
    assert "MINIAODSIM" in title


# -------------------------
# get_abstract
# -------------------------
def test_get_abstract():
    record = {"title": "/DATASET/X/MINIAODSIM"}
    result = CMS_2016_Simulated().get_abstract(None, record)

    assert "description" in result
    assert "DATASET" in result["description"]
