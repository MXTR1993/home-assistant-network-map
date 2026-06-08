"""The Network Map integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_DEVICES,
    SERVICE_UPDATE_POSITION,
    ATTR_DEVICE_ID,
    ATTR_X,
    ATTR_Y,
)
from .coordinator import NetworkMapCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_UPDATE_POSITION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): str,
        vol.Required(ATTR_X): vol.Coerce(float),
        vol.Required(ATTR_Y): vol.Coerce(float),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Network Map component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Network Map from a config entry."""
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    coordinator = NetworkMapCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_update_position(service_call: ServiceCall) -> None:
        """Handle update_position service call."""
        device_id = service_call.data[ATTR_DEVICE_ID]
        x = service_call.data[ATTR_X]
        y = service_call.data[ATTR_Y]

        devices = list(entry.data.get(CONF_DEVICES, []))
        updated = False
        for device in devices:
            if device["device_id"] == device_id:
                device["position_x"] = x
                device["position_y"] = y
                updated = True
                break

        if updated:
            hass.config_entries.async_update_entry(entry, data={CONF_DEVICES: devices})
            await coordinator.async_request_refresh()
            _LOGGER.debug("Updated position for %s to (%s, %s)", device_id, x, y)

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_POSITION,
        async_update_position,
        schema=SERVICE_UPDATE_POSITION_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_POSITION)
    return unload_ok
