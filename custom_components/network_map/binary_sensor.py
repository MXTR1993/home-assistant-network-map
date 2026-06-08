"""Binary sensor platform for Network Map."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICES, DOMAIN
from .coordinator import NetworkMapCoordinator
from .entity import NetworkMapEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    coordinator: NetworkMapCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = entry.data.get(CONF_DEVICES, [])

    entities = [
        NetworkMapDeviceBinarySensor(coordinator, device, entry.entry_id, entry)
        for device in devices
    ]
    async_add_entities(entities)


class NetworkMapDeviceBinarySensor(NetworkMapEntity, BinarySensorEntity):
    """Binary sensor representing a network device online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, device, config_entry_id, config_entry):
        """Initialize the binary sensor."""
        super().__init__(coordinator, device, config_entry_id, config_entry)
        self._device_id = device["device_id"]

    @property
    def _device_data(self) -> dict:
        """Return the current device data from config entry."""
        for d in self._config_entry.data.get(CONF_DEVICES, []):
            if d["device_id"] == self._device_id:
                return d
        return self._device

    @property
    def is_on(self) -> bool:
        """Return True if device is online."""
        data = self.coordinator.data.get(self._device_id)
        return data["online"] if data else False

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        data = self.coordinator.data.get(self._device_id, {})
        device = self._device_data
        return {
            "device_id": device["device_id"],
            "device_type": device.get("device_type", "generic"),
            "ip_address": data.get("ip_address") or device.get("ip_address"),
            "mac_address": device.get("mac_address"),
            "last_seen": data.get("last_seen"),
            "position_x": device.get("position_x", 100),
            "position_y": device.get("position_y", 100),
        }
