# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test for the state.py"""

from ipaddress import IPv4Address

import pytest
from factories import MockCharmFactory  # pylint: disable=import-error

from errors import ConfigurationError
from src.state import (
    BACKENDS_CONFIG_NAME,
    LOCATION_CONFIG_NAME,
    PROTOCOL_CONFIG_NAME,
    Configuration,
)


def test_valid_config():
    """
    arrange: Mock charm with valid configurations.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()

    config = Configuration.from_charm(charm)
    assert config.location == "example.com"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "https"


def test_empty_location():
    """
    arrange: Mock charm with valid configurations.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[LOCATION_CONFIG_NAME] = "   "

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)
    assert str(err.value) == "Empty location configuration found"


@pytest.mark.parametrize(
    "invalid_backends, error_message",
    [
        pytest.param("", "Empty backends configuration found", id="empty backends"),
        pytest.param(
            "mock",
            "Config error: ['mock: value is not a valid IPv4 or IPv6 address']",
            id="incorrect backends format",
        ),
        pytest.param(
            "10.10.1",
            "Config error: ['10.10.1: value is not a valid IPv4 or IPv6 address']",
            id="incorrect IP format",
        ),
    ],
)
def test_config_backends_invalid_backends(invalid_backends: str, error_message: str):
    """
    arrange: Mock charm with invalid backends config.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[BACKENDS_CONFIG_NAME] = invalid_backends

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert str(err.value) == error_message


def test_config_protocol_invalid():
    """
    arrange: Mock charm with invalid protocol config.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROTOCOL_CONFIG_NAME] = "unknown"

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert str(err.value) == "Unknown protocol unknown"


def test_configuration_to_dict():
    """
    arrange: Mock charm with valid configurations.
    act: Create the configuration from the charm, and convert to dict.
    assert:
    """
    charm = MockCharmFactory()

    config = Configuration.from_charm(charm)
    data = config.to_integration_data()
    assert data == {
        "location": "example.com",
        "backends": '["10.10.1.1", "10.10.2.2"]',
        "protocol": "https",
    }
