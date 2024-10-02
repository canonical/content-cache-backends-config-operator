# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The charm state and configurations."""

import json
import logging
import typing

import ops
import pydantic

from errors import ConfigurationError

logger = logging.getLogger(__name__)

HTTP_PROTOCOL_NAME = "http"
HTTPS_PROTOCOL_NAME = "https"
LOCATION_CONFIG_NAME = "location"
BACKENDS_CONFIG_NAME = "backends"


class Backend(pydantic.BaseModel):
    """Represents a single backend.

    Attributes:
        protocol: The protocol to query the backend.
        ip: The IP of the backend.
    """

    protocol: str
    ip: pydantic.IPvAnyAddress
    
    @pydantic.field_validator('protocol')
    @classmethod
    def valid_protocol(cls, value: str) -> str:
        if value not in (HTTP_PROTOCOL_NAME, HTTPS_PROTOCOL_NAME):
            raise ConfigurationError(f"Unknown protocol {value} in backends configuration")
        return value

    @classmethod
    def from_str(cls, backend: str) -> "Backend":
        """Initialize object from a string.

        Args:
            backend: A single backend.

        Raises:
            ConfigurationError: The configuration has errors.

        Returns:
            The object.
        """
        try:
            protocol, ip = [token.strip() for token in backend.split(":")]
        except ValueError as err:
            raise ConfigurationError("Format issue with backends configuration") from err

        return cls(
            protocol=protocol.lower(),
            # Ignore mypy warning as pydantic allows for str to pydantic.IPvAnyAddress.
            ip=ip,  # type: ignore
        )


class Configuration(pydantic.BaseModel):
    """Represents the configuration."""

    location: str
    backends: tuple[Backend, ...]

    @pydantic.field_validator('location')
    @classmethod
    def valid_location(cls, value: str) -> str:
        if not value:
            raise ConfigurationError("Empty location configuration found")
        return value

    @classmethod
    def from_charm(cls, charm: ops.CharmBase) -> "Configuration":
        """Initialize object from the charm.

        Args:
            charm: The charm containing the configuration.

        Returns:
            The object.
        """
        location = typing.cast(str, charm.config.get(LOCATION_CONFIG_NAME, "")).lower().strip()
        
        backends_str = typing.cast(str, charm.config.get(BACKENDS_CONFIG_NAME, "")).strip()
        if not backends_str:
            raise ConfigurationError("Empty backends configuration found")

        try:
            backends = tuple(
                Backend.from_str(token.strip())
                for token in backends_str.split(",")
            )
        except pydantic.ValidationError as err:
            raise ConfigurationError("Unable to parse backends value") from err

        return cls(location=location, backends=backends)

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
