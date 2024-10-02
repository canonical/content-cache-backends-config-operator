#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The content-cache-backends-config charm."""

import logging

import ops

from errors import ConfigurationError
from state import Configuration

logger = logging.getLogger(__name__)

CONFIG_INTEGRATION_NAME = "config"


class ContentCacheBackendsConfigCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework) -> None:
        """Initialize the object."""
        super().__init__(framework)
        framework.observe(self.on.start, self._on_start)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(
            self.on[CONFIG_INTEGRATION_NAME].relation_changed,
            self._on_config_relation_changed,
        )

    def _on_start(self, _: ops.StartEvent) -> None:
        """Handle start event."""
        self.unit.status = ops.BlockedStatus("Waiting for configurations.")

    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        """Handle config changed event."""
        self._load_integration_data()

    def _on_config_relation_changed(self, _: ops.RelationChangedEvent) -> None:
        """Handle config relation changed event."""
        self._load_integration_data()

    def _load_integration_data(self) -> None:
        """Validate the configuration and load to integration."""
        try:
            config = Configuration.from_charm(self)
        except ConfigurationError as err:
            self.unit.status = ops.BlockedStatus(str(err))
            return

        for relation in self.model.relations[CONFIG_INTEGRATION_NAME]:
            relation.data[self.unit].update(config.to_integration_data())
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(ContentCacheBackendsConfigCharm)  # type: ignore
