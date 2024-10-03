# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The charm state and configurations."""

import enum
import json
import logging
import typing

import ops
import pydantic

from errors import ConfigurationError

logger = logging.getLogger(__name__)

LOCATION_CONFIG_NAME = "location"
BACKENDS_CONFIG_NAME = "backends"
PROTOCOL_CONFIG_NAME = "protocol"


class Protocol(str, enum.Enum):
    """Protocol to request backends.

    Attributes:
        HTTP: Use HTTP for requests.
        HTTPS: Use HTTPS for requests.
    """

    HTTP = "http"
    HTTPS = "https"


class Configuration(pydantic.BaseModel):
    """Represents the configuration.

    Attributes:
        location: Defines what URL to match for this set of configuration.
        backends: The backends for this set of configuration.
        protocol: The protocol to request the backends with. Can be http or
            https.
    """

    location: typing.Annotated[str, pydantic.StringConstraints(min_length=1)]
    backends: tuple[pydantic.IPvAnyAddress, ...]
    protocol: Protocol

    @classmethod
    def from_charm(cls, charm: ops.CharmBase) -> "Configuration":
        """Initialize object from the charm.

        Args:
            charm: The charm containing the configuration.

        Raises:
            ConfigurationError: Error with the charm configuration.

        Returns:
            The object.
        """
        location = typing.cast(str, charm.config.get(LOCATION_CONFIG_NAME, "")).strip()
        protocol = typing.cast(str, charm.config.get(PROTOCOL_CONFIG_NAME, "")).lower().strip()
        backends_str = typing.cast(str, charm.config.get(BACKENDS_CONFIG_NAME, "")).strip()
        if not backends_str:
            raise ConfigurationError("Empty backends configuration found")

        backends = tuple(ip.strip() for ip in backends_str.split(","))
        try:
            # Pydantic allows converting str to IPvAnyAddress.
            return cls(location=location, backends=backends, protocol=protocol)  # type: ignore
        except pydantic.ValidationError as err:
            err_msg = [
                f'{error["loc"][0]} = {error["input"]}: {error["msg"]}' for error in err.errors()
            ]
            logger.error("Found config error: %s", err_msg)
            raise ConfigurationError(f"Config error: {err_msg}") from err

    def to_integration_data(self) -> dict[str, str]:
        """Convert to format supported by integration.

        Returns:
            The data in the format accepted by integrations.
        """
        data = json.loads(self.model_dump_json())
        for key, value in data.items():
            if isinstance(value, str):
                continue
            data[key] = json.dumps(value)
        return data
