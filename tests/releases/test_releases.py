import pytest
from cernopendata.modules.releases.models import (
    ReleaseMetadata,
    ReleaseValidationMetadata,
    ReleaseStatus,
)
from cernopendata.modules.releases.api import Release, ReleaseValidation
from cernopendata.modules.releases.validations.base import Validation


@pytest.fixture
def dummy_metadata():
    """Return a fresh ReleaseMetadata object for tests."""
    return ReleaseMetadata(
        name="dummy_release",
        experiment="cms",
        records=[],
        validations=[],
        status=ReleaseStatus.DRAFT.value,
    )


# -----------------------------
# TEST ReleaseValidation
# -----------------------------


def test_release_properties(dummy_metadata):
    """Test Release object properties."""

    release = Release(dummy_metadata)
    assert release.status == dummy_metadata.status
    assert release.records == dummy_metadata.records
    assert len(release.validations) == 0
