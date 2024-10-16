# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test for the state.py"""

from ipaddress import IPv4Address

import pytest
from factories import MockCharmFactory  # pylint: disable=import-error

from errors import ConfigurationError
from src.state import (
    BACKENDS_CONFIG_NAME,
    HOSTNAME_CONFIG_NAME,
    PATH_CONFIG_NAME,
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
    assert config.hostname == "example.com"
    assert config.path == "/"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "https"


def test_http_protocol():
    """
    arrange: Mock charm with valid configurations.
    act: Use a http as protocol, and create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[PROTOCOL_CONFIG_NAME] = "http"

    config = Configuration.from_charm(charm)
    assert config.hostname == "example.com"
    assert config.path == "/"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "http"


def test_longer_path():
    """
    arrange: Mock charm with valid configurations.
    act: Use a longer path, and create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[PATH_CONFIG_NAME] = "/path/to/destination"

    config = Configuration.from_charm(charm)
    assert config.hostname == "example.com"
    assert config.path == "/path/to/destination"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "https"


def test_hostname_with_subdomain():
    """
    arrange: Mock charm with valid configurations.
    act: Use a domain with subdomain as hostname, and create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[HOSTNAME_CONFIG_NAME] = "sub.example.com"

    config = Configuration.from_charm(charm)
    assert config.hostname == "sub.example.com"
    assert config.path == "/"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "https"


def test_empty_hostname():
    """
    arrange: Mock charm with empty hostname.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[HOSTNAME_CONFIG_NAME] = "   "

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)
    assert (
        str(err.value) == "Config error: ['hostname = : String should have at least 1 character']"
    )


def test_long_hostname():
    """
    arrange: Mock charm with long hostname.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[HOSTNAME_CONFIG_NAME] = "a" * 256

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Hostname cannot be longer than 255" in str(err.value)


def test_invalid_hostname():
    """
    arrange: Mock charm with hostname with invalid character.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[HOSTNAME_CONFIG_NAME] = "example?.com"

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "consist of alphanumeric and hyphen" in str(err.value)


def test_empty_path():
    """
    arrange: Mock charm with empty path.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[PATH_CONFIG_NAME] = "   "

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)
    assert str(err.value) == "Config error: ['path = : String should have at least 1 character']"


def test_invalid_path():
    """
    arrange: Mock charm with path with invalid character.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[PATH_CONFIG_NAME] = "/^"

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert (
        str(err.value)
        == "Config error: ['path = /^: Value error, Path contains non-allowed character']"
    )


@pytest.mark.parametrize(
    "invalid_backends, error_message",
    [
        pytest.param("", "Empty backends configuration found", id="empty backends"),
        pytest.param(
            "mock",
            "Config error: ['backends = mock: value is not a valid IPv4 or IPv6 address']",
            id="incorrect backends format",
        ),
        pytest.param(
            "10.10.1",
            "Config error: ['backends = 10.10.1: value is not a valid IPv4 or IPv6 address']",
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

    assert (
        str(err.value)
        == "Config error: [\"protocol = unknown: Input should be 'http' or 'https'\"]"
    )


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
        "hostname": "example.com",
        "path": "/",
        "backends": '["10.10.1.1", "10.10.2.2"]',
        "protocol": "https",
    }
