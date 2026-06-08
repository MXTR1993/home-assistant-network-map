"""Constants for the Network Map integration."""

DOMAIN = "network_map"
PLATFORMS = ["binary_sensor"]
SCAN_INTERVAL = 60

DEVICE_TYPES = [
    "camera",
    "nas",
    "switch",
    "access_point",
    "router",
    "server",
    "generic",
]

DEVICE_TYPE_ICONS = {
    "camera": "mdi:video",
    "nas": "mdi:nas",
    "switch": "mdi:switch",
    "access_point": "mdi:access-point",
    "router": "mdi:router-wireless",
    "server": "mdi:server",
    "generic": "mdi:lan",
}

CONF_DEVICES = "devices"
CONF_DEVICE_TYPE = "device_type"
CONF_POSITION_X = "position_x"
CONF_POSITION_Y = "position_y"

DEFAULT_POSITION = 100

SERVICE_UPDATE_POSITION = "update_position"
ATTR_DEVICE_ID = "device_id"
ATTR_X = "x"
ATTR_Y = "y"
