"""DataUpdateCoordinator for Network Map."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SCAN_INTERVAL, CONF_DEVICES

_LOGGER = logging.getLogger(__name__)


class NetworkMapCoordinator(DataUpdateCoordinator):
    """Coordinator to ping devices and resolve dynamic IPs."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        """Initialize coordinator."""
        self.config_entry = config_entry
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data by pinging devices."""
        devices = self.config_entry.data.get(CONF_DEVICES, [])
        result = {}

        for device in devices:
            device_id = device["device_id"]
            ip = device.get("ip_address")
            mac = device.get("mac_address")
            resolved_ip = ip

            if not resolved_ip and mac:
                resolved_ip = await self._resolve_mac(mac)

            online = False
            if resolved_ip:
                online = await self._ping(resolved_ip)

            result[device_id] = {
                "online": online,
                "ip_address": resolved_ip,
                "last_seen": datetime.now().isoformat() if online else None,
            }

        return result

    async def _ping(self, ip: str) -> bool:
        """Ping a single IP address."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping",
                "-c",
                "1",
                "-W",
                "2",
                ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            return proc.returncode == 0
        except Exception:
            return False

    async def _resolve_mac(self, mac: str) -> str | None:
        """Resolve MAC address to IP via ARP table."""
        # Try /proc/net/arp first
        ip = await self._read_proc_net_arp(mac)
        if ip:
            return ip
        # Fallback to ip neigh
        ip = await self._ip_neigh(mac)
        return ip

    async def _read_proc_net_arp(self, mac: str) -> str | None:
        """Read /proc/net/arp to find IP for MAC."""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._read_file, "/proc/net/arp")
            target = mac.lower()
            for line in data.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 4 and parts[3].lower() == target:
                    return parts[0]
        except Exception:
            pass
        return None

    @staticmethod
    def _read_file(path: str) -> str:
        """Read file content."""
        with open(path, "r") as f:
            return f.read()

    async def _ip_neigh(self, mac: str) -> str | None:
        """Use ip neigh to find IP for MAC."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "neigh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            target = mac.lower()
            for line in stdout.decode().splitlines():
                # Format: 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
                parts = line.split()
                if "lladdr" in parts:
                    try:
                        idx = parts.index("lladdr")
                        if len(parts) > idx + 1 and parts[idx + 1].lower() == target:
                            return parts[0]
                    except ValueError:
                        continue
        except Exception:
            pass
        return None
