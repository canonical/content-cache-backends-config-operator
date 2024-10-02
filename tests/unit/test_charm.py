# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test for the charm."""

from unittest.mock import MagicMock

import ops
import pytest
from ops.testing import Harness

import state
from charm import CONFIG_INTEGRATION_NAME, ContentCacheBackendConfigCharm

SAMPLE_CONFIG = {
    state.LOCATION_CONFIG_NAME: "example.com",
    state.BACKENDS_CONFIG_NAME: "http:10.10.1.1,https:10.1.1.2",
}


def test_start(charm: ContentCacheBackendConfigCharm):
    assert charm.unit.status == ops.BlockedStatus("Waiting for configurations.")


def test_config_config(charm: ContentCacheBackendConfigCharm, harness: Harness):
    """
    arrange: Charm with no integration setup.
    act: Update the configuration with valid values.
    assert: The charm in active status.
    """
    harness.update_config(SAMPLE_CONFIG)

    assert charm.unit.status == ops.ActiveStatus()


@pytest.mark.parametrize(
    "event",
    [
        pytest.param("_on_config_changed", id="config_changed"),
        pytest.param("_on_config_relation_changed", id="config_relation_changed"),
    ],
)
def test_integration_config_missing(
    charm: ContentCacheBackendConfigCharm, harness: Harness, event: str
):
    mock_event = MagicMock()
    getattr(charm, event)(mock_event)

    assert isinstance(charm.unit.status, ops.BlockedStatus)


@pytest.mark.parametrize(
    "event",
    [
        pytest.param("_on_config_changed", id="config_changed"),
        pytest.param("_on_config_relation_changed", id="config_relation_changed"),
    ],
)
def test_integration_data(charm: ContentCacheBackendConfigCharm, harness: Harness, event: str):
    harness.update_config(SAMPLE_CONFIG)

    relation_id = harness.add_relation(
        CONFIG_INTEGRATION_NAME,
        remote_app="content-cache",
    )
    harness.add_relation_unit(relation_id, remote_unit_name="content-cache/0")

    mock_event = MagicMock()
    getattr(charm, event)(mock_event)

    data = harness.get_relation_data(relation_id, app_or_unit=charm.unit.name)
    assert charm.unit.status == ops.ActiveStatus()
    assert data == {
        "location": "example.com",
        "backends": '[{"protocol": "http", "ip": "10.10.1.1"}, {"protocol": "https", "ip": "10.1.1.2"}]',
    }
