#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The content-cache-backends-config charm."""

import logging

import ops

from errors import ConfigurationError
from state import Configuration

logger = logging.getLogger(__name__)

CONFIG_INTEGRATION_NAME = "cache-config"


class ContentCacheBackendsConfigCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework) -> None:
        """Initialize the object.

        Args:
            framework: The ops framework.
        """
        super().__init__(framework)
        framework.observe(self.on.start, self._on_start)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(
            self.on[CONFIG_INTEGRATION_NAME].relation_changed,
            self._on_cache_config_relation_changed,
        )
        framework.observe(
            self.on[CONFIG_INTEGRATION_NAME].relation_broken,
            self._on_cache_config_relation_broken,
        )

    def _on_start(self, _: ops.StartEvent) -> None:
        """Handle start event."""
        self._set_status()

    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        """Handle config changed event."""
        self._load_integration_data()

    def _on_cache_config_relation_changed(self, _: ops.RelationChangedEvent) -> None:
        """Handle cache config relation changed event."""
        self._load_integration_data()

    def _on_cache_config_relation_broken(self, _: ops.RelationBrokenEvent) -> None:
        """Handle cache config relation broken event."""
        self._set_status()

    def _load_integration_data(self) -> None:
        """Validate the configuration and load to integration."""
        if not self.unit.is_leader():
            logger.debug("Not leader: not setting the integration data")
            return

        logger.info("Leader: loading configuration")
        try:
            config = Configuration.from_charm(self)
        except ConfigurationError as err:
            logger.error("Configuration error: %s", err)
            self.unit.status = ops.BlockedStatus(str(err))
            return

        logger.info("Leader: setting integration data")
        if self.model.relations[CONFIG_INTEGRATION_NAME]:
            rel = self.model.relations[CONFIG_INTEGRATION_NAME][0]
            rel.data[self.app].update(config.to_integration_data())
        logger.info("Leader: integration data set")
        self._set_status()

    def _set_status(self):
        """Set the charm status."""
        if not self.model.relations[CONFIG_INTEGRATION_NAME]:
            logger.info("No integration found")
            self.unit.status = ops.BlockedStatus("Waiting for integration")
            return
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(ContentCacheBackendsConfigCharm)  # type: ignore
