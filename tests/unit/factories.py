# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import typing
from unittest.mock import MagicMock

import factory

from src.state import BACKENDS_CONFIG_NAME, LOCATION_CONFIG_NAME, PROTOCOL_CONFIG_NAME 

T = typing.TypeVar("T")


class MockUnitFactory(factory.Factory):
    """Mock charm unit."""

    class Meta:
        """Configuration for factory."""

        model = MagicMock

    name: str


class MockCharmFactory(factory.Factory):
    """Mock the content-cache-backend-config charm."""

    class Meta:
        """Configuration for the factory."""

        model = MagicMock

    app = MagicMock
    unit = MockUnitFactory
    config = factory.Dict(
        {
            LOCATION_CONFIG_NAME: "example.com",
            BACKENDS_CONFIG_NAME: "10.10.1.1, 10.10.2.2",
            PROTOCOL_CONFIG_NAME: "https"
        }
    )
