from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases.models import ReleaseStatus
from cernopendata.modules.releases.validations.slug import ValidSlug


class DummyRelease:
    def __init__(self, documents, status="DRAFT"):
        self.documents = documents
        self.status = ReleaseStatus[status].value


@pytest.mark.parametrize(
    "documents, expected_error_fragment",
    [
        ([{"title": "no slug"}], "Missing or empty"),
        ([{"slug": ""}], "Missing or empty"),
        ([{"slug": "a"}, {"slug": "a"}], "Duplicate slug"),
    ],
)
def test_validate_reports_error(documents, expected_error_fragment):
    validator = ValidSlug()
    release = DummyRelease(documents)
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert any(expected_error_fragment in e for e in errors)


def test_validate_passes_with_unique_slug():
    validator = ValidSlug()
    release = DummyRelease([{"slug": "alice-data-2015"}])
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert errors == []


def test_validate_reports_already_registered_pid():
    validator = ValidSlug()
    release = DummyRelease([{"slug": "alice-data-2015"}])
    with patch.object(validator, "_duplicate_pids", return_value=["alice-data-2015"]):
        errors = validator.validate(release)
    assert any("already registered" in e for e in errors)


def test_validate_staged_release_skips_pid_check():
    validator = ValidSlug()
    release = DummyRelease([{"slug": "alice-data-2015"}], status="STAGED")
    spy = MagicMock(return_value=[])
    validator._duplicate_pids = spy
    errors = validator.validate(release)
    spy.assert_not_called()
    assert errors == []


def test_validate_no_documents():
    validator = ValidSlug()
    release = DummyRelease([])
    with patch.object(validator, "_duplicate_pids", return_value=[]):
        errors = validator.validate(release)
    assert errors == []


def test_fix_derives_slug_from_source_filename():
    validator = ValidSlug()
    release = DummyRelease(
        [{"_source_filename": "alice-releases-educational-datasets-2015.json"}]
    )
    errors = validator.fix(release)
    assert errors == []
    assert release.documents[0]["slug"] == "alice-releases-educational-datasets-2015"


def test_fix_does_not_overwrite_existing_slug():
    validator = ValidSlug()
    release = DummyRelease([{"slug": "already-set", "_source_filename": "other.json"}])
    errors = validator.fix(release)
    assert errors == []
    assert release.documents[0]["slug"] == "already-set"


def test_fix_no_source_filename_returns_error():
    validator = ValidSlug()
    release = DummyRelease([{"title": "no slug, no source"}])
    errors = validator.fix(release)
    assert any("Cannot auto-fix" in e for e in errors)


def test_fix_strips_path_prefix_from_source_filename():
    validator = ValidSlug()
    release = DummyRelease([{"_source_filename": "some/path/my-doc.json"}])
    errors = validator.fix(release)
    assert errors == []
    assert release.documents[0]["slug"] == "my-doc"
