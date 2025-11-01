"""Discover UberSolar devices."""

from __future__ import annotations

import asyncio
import logging

import bleak

from .const import DEFAULT_SCAN_TIMEOUT
from .models import UberSolarAdvertisement

_LOGGER = logging.getLogger(__name__)
CONNECT_LOCK = asyncio.Lock()


class GetUberSolarDevices:
    """Scan for all UberSolar devices."""

    def __init__(self, interface: int = 0) -> None:
        """Get UberSolar devices class constructor."""
        self._interface = f"hci{interface}"
        self._adv_data: dict[str, UberSolarAdvertisement] = {}

    def detection_callback(
        self,
        device: bleak.backends.device.BLEDevice,
        advertisement_data: bleak.backends.scanner.AdvertisementData,
    ) -> None:
        """BTLE adv scan callback."""

        name = device.name or advertisement_data.local_name
        if not name or "UberSmart_" not in name:
            return

        discovery = UberSolarAdvertisement(
            device.address, device.name or name, device, advertisement_data.rssi, True
        )
        self._adv_data[discovery.address] = discovery

    async def discover(
        self, scan_timeout: int = DEFAULT_SCAN_TIMEOUT
    ) -> dict[str, UberSolarAdvertisement]:
        """Find UberSolar devices."""

        scanner = bleak.BleakScanner(
            adapter=self._interface,
            detection_callback=self.detection_callback,
        )

        async with CONNECT_LOCK:
            await scanner.start()
            await asyncio.sleep(scan_timeout)
            await scanner.stop()

        return self._adv_data

    async def get_device_data(
        self, address: str
    ) -> dict[str, UberSolarAdvertisement] | None:
        """Return data for specific device."""
        if not self._adv_data:
            await self.discover()

        return {
            device: adv
            for device, adv in self._adv_data.items()
            # MacOS uses UUIDs instead of MAC addresses
            if address in {adv.address, adv.device.address}
        }
