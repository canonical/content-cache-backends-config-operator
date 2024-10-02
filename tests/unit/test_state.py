# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from ipaddress import IPv4Address

import pytest
from factories import MockCharmFactory
from pydantic import IPvAnyAddress

from errors import ConfigurationError
from state import BACKENDS_CONFIG_NAME, LOCATION_CONFIG_NAME, Backend, Configuration


def test_valid_config():
    """
    arrange: Mock charm with valid configurations.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()

    config = Configuration.from_charm(charm)
    assert config.location == "example.com"
    assert config.backends == (
        Backend(protocol="http", ip=IPv4Address("10.10.1.1")),
        Backend(protocol="https", ip=IPv4Address("10.10.2.2")),
    )

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
        pytest.param("asdf", "Format issue with backends configuration", id="incorrect backends format"),
        pytest.param("http:10.10.1", "Unable to parse backends value", id="incorrect IP format"),
        pytest.param(
            "kafka:10.10.10.10",
            "Unknown protocol kafka in backends configuration",
            id="unknown protocol",
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
        "backends": '[{"protocol": "http", "ip": "10.10.1.1"}, {"protocol": "https", "ip": "10.10.2.2"}]',
    }
