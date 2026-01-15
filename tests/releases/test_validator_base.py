import pytest

from cernopendata.modules.releases.validations import Validation


def test_validate_not_implemented():
    """Base validate should raise."""
    v = Validation()
    with pytest.raises(NotImplementedError):
        v.validate(None)


def test_fix_not_implemented():
    """Base fix should raise."""
    v = Validation()
    with pytest.raises(NotImplementedError):
        v.fix(None)


def test_subclass_registration():
    """Subclass should automatically register."""
    initial_len = len(Validation.registry)

    class DummyValidation(Validation):
        def validate(self, release):
            pass

    assert len(Validation.registry) == initial_len + 1
    assert DummyValidation in Validation.registry


def test_fixable_false_when_not_overridden():
    """Validation without fix override should not be fixable."""

    class NoFixValidation(Validation):
        def validate(self, release):
            pass

    v = NoFixValidation()
    assert v.fixable is False


def test_fixable_true_when_overridden():
    """Validation with fix override should be fixable."""

    class FixValidation(Validation):
        def validate(self, release):
            pass

        def fix(self, release):
            pass

    v = FixValidation()
    assert v.fixable is True
