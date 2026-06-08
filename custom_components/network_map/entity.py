"""Base entity for Network Map."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEVICE_TYPE_ICONS
from .coordinator import NetworkMapCoordinator


class NetworkMapEntity(CoordinatorEntity):
    """Base entity for a network device."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: NetworkMapCoordinator, device: dict, config_entry_id: str, config_entry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = device
        self._config_entry_id = config_entry_id
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry_id}_{device['device_id']}"
        self._attr_name = device["name"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{config_entry_id}_{device['device_id']}")},
            "name": device["name"],
            "model": device.get("device_type", "generic").replace("_", " ").title(),
        }

    @property
    def device_type(self) -> str:
        """Return device type."""
        return self._device.get("device_type", "generic")

    @property
    def icon(self) -> str | None:
        """Return icon based on device type."""
        return DEVICE_TYPE_ICONS.get(self.device_type)
