# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test for the charm."""

from unittest.mock import MagicMock

import ops
import pytest
from ops.testing import Harness

import state
from charm import CONFIG_INTEGRATION_NAME, ContentCacheBackendsConfigCharm

SAMPLE_CONFIG = {
    state.LOCATION_CONFIG_NAME: "example.com",
    state.BACKENDS_CONFIG_NAME: "10.10.1.1,10.1.1.2",
    state.PROTOCOL_CONFIG_NAME: "https",
}


def test_start(charm: ContentCacheBackendsConfigCharm):
    """
    arrange: A working charm.
    act: The charm started.
    assert: Charm in block state.
    """
    assert charm.unit.status == ops.BlockedStatus("Waiting for integration")


def test_config_no_integration(charm: ContentCacheBackendsConfigCharm, harness: Harness):
    """
    arrange: Charm with no integration.
    act: Update the configuration with valid values.
    assert: The charm in active status.
    """
    harness.update_config(SAMPLE_CONFIG)
    assert charm.unit.status == ops.BlockedStatus("Waiting for integration")


@pytest.mark.parametrize(
    "event",
    [
        pytest.param("_on_config_changed", id="config_changed"),
        pytest.param("_on_cache_config_relation_changed", id="config_relation_changed"),
    ],
)
def test_integration_config_missing(charm: ContentCacheBackendsConfigCharm, event: str):
    """
    arrange: Charm with no integration.
    act: Trigger events.
    assert: Charm in block state.
    """
    mock_event = MagicMock()
    getattr(charm, event)(mock_event)

    assert isinstance(charm.unit.status, ops.BlockedStatus)

@pytest.mark.parametrize(
    "event",
    [
        pytest.param("_on_config_changed", id="config_changed"),
        pytest.param("_on_cache_config_relation_changed", id="config_relation_changed"),
    ],
)
def test_integration_data_not_leader(charm: ContentCacheBackendsConfigCharm, harness: Harness, event: str):
    """
    arrange: Follow unit with configurations and integration.
    act: Trigger events.
    assert: The integration has no data.
    """
    harness.set_leader(False)
    harness.update_config(SAMPLE_CONFIG)

    relation_id = harness.add_relation(
        CONFIG_INTEGRATION_NAME,
        remote_app="content-cache",
    )
    harness.add_relation_unit(relation_id, remote_unit_name="content-cache/0")

    mock_event = MagicMock()
    getattr(charm, event)(mock_event)

    data = harness.get_relation_data(relation_id, app_or_unit=charm.app.name)
    assert charm.unit.status == ops.BlockedStatus('Waiting for integration')
    assert data == {}


@pytest.mark.parametrize(
    "event",
    [
        pytest.param("_on_config_changed", id="config_changed"),
        pytest.param("_on_cache_config_relation_changed", id="config_relation_changed"),
    ],
)
def test_integration_data(charm: ContentCacheBackendsConfigCharm, harness: Harness, event: str):
    """
    arrange: Leader unit with configurations and integration.
    act: Trigger events.
    assert: The configuration is in the databag.
    """
    harness.update_config(SAMPLE_CONFIG)

    relation_id = harness.add_relation(
        CONFIG_INTEGRATION_NAME,
        remote_app="content-cache",
    )
    harness.add_relation_unit(relation_id, remote_unit_name="content-cache/0")

    mock_event = MagicMock()
    getattr(charm, event)(mock_event)

    data = harness.get_relation_data(relation_id, app_or_unit=charm.app.name)
    assert charm.unit.status == ops.ActiveStatus()
    assert data == {
        "location": "example.com",
        "backends": '["10.10.1.1", "10.1.1.2"]',
        "protocol": "https",
    }

@pytest.mark.parametrize(
    "is_leader",
    [
        pytest.param(True, id="leader"),
        pytest.param(False, id="follower"),
    ],
)
def test_integration_removed(harness: Harness, charm: ContentCacheBackendsConfigCharm, is_leader: bool):
    """
    arrange: Unit with integration.
    act: Remove integration.
    assert: Block status
    """
    harness.set_leader(is_leader)
    harness.update_config(SAMPLE_CONFIG)

    relation_id = harness.add_relation(
        CONFIG_INTEGRATION_NAME,
        remote_app="content-cache",
    )
    harness.add_relation_unit(relation_id, remote_unit_name="content-cache/0")
    
    harness.remove_relation(relation_id)
    
    assert charm.unit.status == ops.BlockedStatus('Waiting for integration')
