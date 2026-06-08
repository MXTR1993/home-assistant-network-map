"""Config flow for Network Map integration."""
from __future__ import annotations

import re
import ipaddress
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    DEVICE_TYPES,
    CONF_DEVICES,
    CONF_DEVICE_TYPE,
    CONF_POSITION_X,
    CONF_POSITION_Y,
    DEFAULT_POSITION,
)


def slugify_name(name: str) -> str:
    """Create a simple slug from a name."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
    return slug or "device"


def validate_mac(mac: str | None) -> str | None:
    """Validate and normalize MAC address."""
    if not mac:
        return None
    mac = mac.strip().lower()
    # Support aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff
    if re.fullmatch(r"([0-9a-f]{2}[:-]){5}[0-9a-f]{2}", mac):
        return mac.replace("-", ":")
    if re.fullmatch(r"[0-9a-f]{12}", mac):
        return ":".join(mac[i : i + 2] for i in range(0, 12, 2))
    return None


def validate_ip(ip: str | None) -> str | None:
    """Validate IP address."""
    if not ip:
        return None
    ip = ip.strip()
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        return None


DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        vol.Required(CONF_DEVICE_TYPE, default="generic"): SelectSelector(
            SelectSelectorConfig(options=DEVICE_TYPES)
        ),
        vol.Optional("ip_address"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        vol.Optional("mac_address"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        vol.Optional(CONF_POSITION_X, default=DEFAULT_POSITION): NumberSelector(
            NumberSelectorConfig(min=0, max=2000, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_POSITION_Y, default=DEFAULT_POSITION): NumberSelector(
            NumberSelectorConfig(min=0, max=2000, mode=NumberSelectorMode.BOX)
        ),
    }
)


class NetworkMapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Network Map."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            name = user_input["name"].strip()
            device_id = slugify_name(name)
            ip = validate_ip(user_input.get("ip_address"))
            mac = validate_mac(user_input.get("mac_address"))

            if not ip and not mac:
                errors["base"] = "need_ip_or_mac"
            elif user_input.get("ip_address") and not ip:
                errors["ip_address"] = "invalid_ip"
            elif user_input.get("mac_address") and not mac:
                errors["mac_address"] = "invalid_mac"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                device = {
                    "device_id": device_id,
                    "name": name,
                    CONF_DEVICE_TYPE: user_input[CONF_DEVICE_TYPE],
                    "ip_address": ip,
                    "mac_address": mac,
                    CONF_POSITION_X: user_input.get(CONF_POSITION_X, DEFAULT_POSITION),
                    CONF_POSITION_Y: user_input.get(CONF_POSITION_Y, DEFAULT_POSITION),
                }

                return self.async_create_entry(
                    title="Network Map",
                    data={CONF_DEVICES: [device]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DEVICE_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> NetworkMapOptionsFlowHandler:
        """Get the options flow for this handler."""
        return NetworkMapOptionsFlowHandler(config_entry)


class NetworkMapOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Network Map."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.devices: list[dict[str, Any]] = list(config_entry.data.get(CONF_DEVICES, []))

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_device", "edit_select", "delete_device"],
        )

    async def async_step_add_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Add a new device."""
        errors = {}

        if user_input is not None:
            name = user_input["name"].strip()
            device_id = slugify_name(name)
            # ensure unique device_id
            existing_ids = {d["device_id"] for d in self.devices}
            base_id = device_id
            counter = 1
            while device_id in existing_ids:
                device_id = f"{base_id}_{counter}"
                counter += 1

            ip = validate_ip(user_input.get("ip_address"))
            mac = validate_mac(user_input.get("mac_address"))

            if not ip and not mac:
                errors["base"] = "need_ip_or_mac"
            elif user_input.get("ip_address") and not ip:
                errors["ip_address"] = "invalid_ip"
            elif user_input.get("mac_address") and not mac:
                errors["mac_address"] = "invalid_mac"
            else:
                device = {
                    "device_id": device_id,
                    "name": name,
                    CONF_DEVICE_TYPE: user_input[CONF_DEVICE_TYPE],
                    "ip_address": ip,
                    "mac_address": mac,
                    CONF_POSITION_X: user_input.get(CONF_POSITION_X, DEFAULT_POSITION),
                    CONF_POSITION_Y: user_input.get(CONF_POSITION_Y, DEFAULT_POSITION),
                }
                self.devices.append(device)
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data={CONF_DEVICES: self.devices}
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_device",
            data_schema=DEVICE_SCHEMA,
            errors=errors,
        )

    async def async_step_edit_select(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select device to edit."""
        if not self.devices:
            return self.async_abort(reason="no_devices")

        options = {d["device_id"]: d["name"] for d in self.devices}

        if user_input is not None:
            return await self.async_step_edit_device(device_id=user_input["device_id"])

        schema = vol.Schema(
            {
                vol.Required("device_id"): SelectSelector(
                    SelectSelectorConfig(options=list(options.keys()))
                ),
            }
        )
        return self.async_show_form(step_id="edit_select", data_schema=schema)

    async def async_step_edit_device(self, user_input: dict[str, Any] | None = None, device_id: str | None = None) -> FlowResult:
        """Edit a device."""
        if device_id:
            self._edit_device_id = device_id
        else:
            device_id = self._edit_device_id

        device = next((d for d in self.devices if d["device_id"] == device_id), None)
        if device is None:
            return self.async_abort(reason="device_not_found")

        errors = {}

        if user_input is not None:
            name = user_input["name"].strip()
            ip = validate_ip(user_input.get("ip_address"))
            mac = validate_mac(user_input.get("mac_address"))

            if not ip and not mac:
                errors["base"] = "need_ip_or_mac"
            elif user_input.get("ip_address") and not ip:
                errors["ip_address"] = "invalid_ip"
            elif user_input.get("mac_address") and not mac:
                errors["mac_address"] = "invalid_mac"
            else:
                device["name"] = name
                device[CONF_DEVICE_TYPE] = user_input[CONF_DEVICE_TYPE]
                device["ip_address"] = ip
                device["mac_address"] = mac
                device[CONF_POSITION_X] = user_input.get(CONF_POSITION_X, DEFAULT_POSITION)
                device[CONF_POSITION_Y] = user_input.get(CONF_POSITION_Y, DEFAULT_POSITION)
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data={CONF_DEVICES: self.devices}
                )
                return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Required("name", default=device["name"]): TextSelector(),
                vol.Required(CONF_DEVICE_TYPE, default=device.get(CONF_DEVICE_TYPE, "generic")): SelectSelector(
                    SelectSelectorConfig(options=DEVICE_TYPES)
                ),
                vol.Optional("ip_address", default=device.get("ip_address", "")): TextSelector(),
                vol.Optional("mac_address", default=device.get("mac_address", "")): TextSelector(),
                vol.Optional(CONF_POSITION_X, default=device.get(CONF_POSITION_X, DEFAULT_POSITION)): NumberSelector(
                    NumberSelectorConfig(min=0, max=2000, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_POSITION_Y, default=device.get(CONF_POSITION_Y, DEFAULT_POSITION)): NumberSelector(
                    NumberSelectorConfig(min=0, max=2000, mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="edit_device",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_delete_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Delete a device."""
        if not self.devices:
            return self.async_abort(reason="no_devices")

        options = {d["device_id"]: d["name"] for d in self.devices}

        if user_input is not None:
            self.devices = [d for d in self.devices if d["device_id"] != user_input["device_id"]]
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={CONF_DEVICES: self.devices}
            )
            return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Required("device_id"): SelectSelector(
                    SelectSelectorConfig(options=list(options.keys()))
                ),
            }
        )
        return self.async_show_form(step_id="delete_device", data_schema=schema)
