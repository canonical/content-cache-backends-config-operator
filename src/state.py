# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The charm state and configurations."""

import enum
import json
import logging
import re
import typing

import ops
import pydantic

from errors import ConfigurationError

logger = logging.getLogger(__name__)

HOSTNAME_CONFIG_NAME = "hostname"
PATH_CONFIG_NAME = "path"
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
        hostname: The hostname for the virtual host for this set of configuration.
        path: The path for this set of configuration.
        backends: The backends for this set of configuration.
        protocol: The protocol to request the backends with. Can be http or
            https.
    """

    hostname: typing.Annotated[str, pydantic.StringConstraints(min_length=1)]
    path: typing.Annotated[str, pydantic.StringConstraints(min_length=1)]
    backends: tuple[pydantic.IPvAnyAddress, ...]
    protocol: Protocol

    @pydantic.field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str) -> str:
        """Validate the hostname.

        Args:
            value: The value to validate.

        Raises:
            ValueError: The validation failed.

        Returns:
            The value after validation.
        """
        if len(value) > 255:
            raise ValueError("Hostname cannot be longer than 255")

        valid_segment = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        for segment in value.split("."):
            if valid_segment.fullmatch(segment) is None:
                raise ValueError(
                    (
                        "Each Hostname segment must be less than 64 in length, and consist of "
                        "alphanumeric and hyphen"
                    )
                )

        return value

    @pydantic.field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Validate the path.

        Args:
            value: The value to validate.

        Raises:
            ValueError: The validation failed.

        Returns:
            The value after validation.
        """
        # This are the valid characters for path in addition to `/`:
        # a-z A-Z 0-9 . - _ ~ ! $ & ' ( ) * + , ; = : @
        # https://datatracker.ietf.org/doc/html/rfc3986#section-3.3
        valid_path = re.compile(r"[/A-Z0-9.\-_~!$&'()*+,;=:@]+", re.IGNORECASE)
        if valid_path.fullmatch(value) is None:
            raise ValueError("Path contains non-allowed character")
        return value

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
        hostname = typing.cast(str, charm.config.get(HOSTNAME_CONFIG_NAME, "")).strip()
        path = typing.cast(str, charm.config.get(PATH_CONFIG_NAME, "")).strip()
        protocol = typing.cast(str, charm.config.get(PROTOCOL_CONFIG_NAME, "")).lower().strip()
        backends_str = typing.cast(str, charm.config.get(BACKENDS_CONFIG_NAME, "")).strip()
        if not backends_str:
            raise ConfigurationError("Empty backends configuration found")

        backends = tuple(ip.strip() for ip in backends_str.split(","))
        try:
            return cls(
                hostname=hostname,
                path=path,
                # Pydantic allows converting str to IPvAnyAddress.
                backends=backends,  # type: ignore
                # Pydantic allows converting str to a string enum.
                protocol=protocol,  # type: ignore
            )
        except pydantic.ValidationError as err:
            err_msg = [
                f'{error["loc"][0]} = {error["input"]}: {error["msg"]}' for error in err.errors()
            ]
            logger.error("Found config error: %s", err_msg)
            raise ConfigurationError(f"Config error: {err_msg}") from err

    def to_integration_data(self) -> dict[str, str]:
        """Convert to format supported by integration.

        Juju integration only supports data of dict[str, str] type.
        This method ensures the the values in the dict are all str type.

        Returns:
            The data in the format accepted by integrations.
        """
        data = json.loads(self.model_dump_json())
        for key, value in data.items():
            if isinstance(value, str):
                continue
            data[key] = json.dumps(value)
        return data
