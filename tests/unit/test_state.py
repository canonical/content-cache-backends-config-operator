# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit test for the state.py"""

from ipaddress import IPv4Address

import pydantic_core
import pytest
from factories import MockCharmFactory  # pylint: disable=import-error

from errors import ConfigurationError
from src.state import (
    BACKENDS_CONFIG_NAME,
    BACKENDS_PATH_CONFIG_NAME,
    HEALTH_CHECK_PATH_CONFIG_NAME,
    HOSTNAME_CONFIG_NAME,
    PATH_CONFIG_NAME,
    PROTOCOL_CONFIG_NAME,
    PROXY_CACHE_VALID_CONFIG_NAME,
    Configuration,
)


def mock_error_model_dump_json(_):
    """Mock error in model_dump_json of pydantic.BaseModel.

    Raises:
        PydanticSerializationError: Mock error.
    """
    raise pydantic_core.PydanticSerializationError("mock error")


def mock_error_json_dumps(_):
    """Mock error in json.dumps.

    Raises:
        ValueError: Mock error.
    """
    raise ValueError("mock error")


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
    assert config.health_check_path == "/"
    assert config.health_check_interval == 30
    assert config.backends_path == "/"
    assert config.proxy_cache_valid == ()


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
    assert config.health_check_path == "/"
    assert config.health_check_interval == 30
    assert config.backends_path == "/"
    assert config.proxy_cache_valid == ()


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


def test_longer_path():
    """
    arrange: Mock charm with valid configurations.
    act: Use a longer path, and create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[PATH_CONFIG_NAME] = "/path/to/destination/0"
    charm.config[HEALTH_CHECK_PATH_CONFIG_NAME] = "/path/to/destination/1"
    charm.config[BACKENDS_PATH_CONFIG_NAME] = "/path/to/destination/2"

    config = Configuration.from_charm(charm)
    assert config.hostname == "example.com"
    assert config.path == "/path/to/destination/0"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "https"
    assert config.health_check_path == "/path/to/destination/1"
    assert config.health_check_interval == 30
    assert config.backends_path == "/path/to/destination/2"
    assert config.proxy_cache_valid == ()


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


def test_invalid_health_check_path():
    """
    arrange: Mock charm with path with invalid character.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[HEALTH_CHECK_PATH_CONFIG_NAME] = "/path/to/`"

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert (
        "'health_check_path = /path/to/`: Value error, Path contains non-allowed character'"
        in str(err.value)
    )


def test_invalid_backends_path():
    """
    arrange: Mock charm with path with invalid character.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[BACKENDS_PATH_CONFIG_NAME] = "/path/{"

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "backends_path = /path/{: Value error, Path contains non-allowed character" in str(
        err.value
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
    assert config.health_check_path == "/"
    assert config.health_check_interval == 30
    assert config.backends_path == "/"
    assert config.proxy_cache_valid == ()


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


def test_invalid_format_proxy_cache_valid():
    """
    arrange: Mock charm with invalid cache valid config.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = "invalid"

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Unable to parse proxy_cache_valid: invalid" in str(err.value)


def test_without_time_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config with time.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["200"]'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Invalid item in proxy_cache_valid: 200" in str(err.value)


def test_non_list_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config that is not a list.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '{"hello": 10}'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert 'The proxy_cache_valid is not a list: {"hello": 10}' in str(err.value)


def test_invalid_time_str_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config of invalid time string.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["200 302 1y"]'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Invalid time for proxy_cache_valid: 1y" in str(err.value)


def test_non_int_time_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config with non int time.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["200 302 tend"]'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Non-int time in proxy_cache_valid: tend" in str(err.value)


def test_negative_time_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config with negative time.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["200 302 -10d"]'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Time must be positive int for proxy_cache_valid: -10d" in str(err.value)


def test_non_int_status_code_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config with non-int status code.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["ok 30m"]'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Non-int status code in proxy_cache_valid: ok" in str(err.value)


def test_invalid_status_code_proxy_cache_valid():
    """
    arrange: Mock charm with cache valid config with invalid status code.
    act: Create the state from the charm.
    assert: Configuration error raised with a correct error message.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["200 99 30m"]'

    with pytest.raises(ConfigurationError) as err:
        Configuration.from_charm(charm)

    assert "Value error, Invalid status code in proxy_cache_valid: 99" in str(err.value)


def test_valid_proxy_cache_valid():
    """
    arrange: Mock charm with valid complex proxy_cache_valid configuration.
    act: Create the configuration from the charm.
    assert: Correct configurations from the mock charm.
    """
    charm = MockCharmFactory()
    charm.config[PROXY_CACHE_VALID_CONFIG_NAME] = '["200 302 30m", "400 1m", "500 1m"]'

    config = Configuration.from_charm(charm)
    assert config.hostname == "example.com"
    assert config.path == "/"
    assert config.backends == (IPv4Address("10.10.1.1"), IPv4Address("10.10.2.2"))
    assert config.protocol == "https"
    assert config.health_check_path == "/"
    assert config.health_check_interval == 30
    assert config.backends_path == "/"
    assert config.proxy_cache_valid == ("200 302 30m", "400 1m", "500 1m")


def test_configuration_to_data():
    """
    arrange: Mock charm with valid configurations.
    act: Create the configuration from the charm, and convert to dict.
    assert: Data contains the configurations.
    """
    charm = MockCharmFactory()

    config = Configuration.from_charm(charm)
    data = config.to_integration_data()
    assert data == {
        "hostname": "example.com",
        "path": "/",
        "backends": '["10.10.1.1", "10.10.2.2"]',
        "protocol": "https",
        "health_check_path": "/",
        "health_check_interval": "30",
        "backends_path": "/",
        "proxy_cache_valid": "[]",
    }


def test_configuration_to_data_model_dump_error(monkeypatch):
    """
    arrange: Mock model_dump_json to raise error.
    act: Create the configuration from the charm, and convert to dict.
    assert: Error raised with the correct error message.
    """
    monkeypatch.setattr("state.pydantic.BaseModel.model_dump_json", mock_error_model_dump_json)
    charm = MockCharmFactory()

    config = Configuration.from_charm(charm)

    with pytest.raises(ConfigurationError) as err:
        config.to_integration_data()

    assert "Unable to convert configuration to integration data format" in str(err.value)


def test_configuration_to_json_dumps_error(monkeypatch):
    """
    arrange: Mock json.dumps to raise error.
    act: Create the configuration from the charm, and convert to dict.
    assert: Error raised with the correct error message.
    """
    monkeypatch.setattr("state.json.dumps", mock_error_json_dumps)
    charm = MockCharmFactory()

    config = Configuration.from_charm(charm)

    with pytest.raises(ConfigurationError) as err:
        config.to_integration_data()

    assert "Unable to convert configuration to integration data format" in str(err.value)
