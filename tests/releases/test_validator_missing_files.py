from cernopendata.modules.releases.validations.missing_files import MissingFiles


class DummyRelease:
    def __init__(self, records):
        self.records = records


def test_reports_files_but_none_provided():
    release = DummyRelease([{"distribution": {"number_files": 423}}])

    errors = MissingFiles().validate(release)

    assert errors == ["Entry 1 reports having 423 files but none were provided."]


def test_files_provided():
    release = DummyRelease(
        [{"distribution": {"number_files": 1}, "files": [{"uri": "a"}]}]
    )

    assert MissingFiles().validate(release) == []


def test_index_files_count_as_provided():
    release = DummyRelease(
        [
            {
                "distribution": {"number_files": 1000},
                "files": [{"uri": "index.json", "type": "index.json"}],
            }
        ]
    )

    assert MissingFiles().validate(release) == []


def test_rucio_dataset_is_exempt():
    release = DummyRelease(
        [{"distribution": {"number_files": 423}, "rucio_dataset": "cms:/foo/bar"}]
    )

    assert MissingFiles().validate(release) == []


def test_no_distribution():
    release = DummyRelease([{}])

    assert MissingFiles().validate(release) == []


def test_zero_files_declared():
    release = DummyRelease([{"distribution": {"number_files": 0}}])

    assert MissingFiles().validate(release) == []


def test_only_offending_entries_flagged():
    release = DummyRelease(
        [
            {"distribution": {"number_files": 1}, "files": [{"uri": "a"}]},
            {"distribution": {"number_files": 5}},
        ]
    )

    errors = MissingFiles().validate(release)

    assert errors == ["Entry 2 reports having 5 files but none were provided."]
