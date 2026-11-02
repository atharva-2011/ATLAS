"""Tests for atlas_common package."""

from atlas_common import APP_NAME, ENV_LOCAL, SUPPORTED_ENVIRONMENTS


def test_constants():
    assert APP_NAME == "ATLAS"
    assert ENV_LOCAL in SUPPORTED_ENVIRONMENTS
    assert len(SUPPORTED_ENVIRONMENTS) == 4
