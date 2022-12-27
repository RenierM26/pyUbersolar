"""Discover UberSolar devices."""

from __future__ import annotations

import asyncio
import logging

import bleak

from .const import DEFAULT_RETRY_COUNT, DEFAULT_RETRY_TIMEOUT, DEFAULT_SCAN_TIMEOUT
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

        if "UberSmart_" in device.name:
            discovery = UberSolarAdvertisement(
                device.address, device.name, device, advertisement_data.rssi, True
            )
            if discovery:
                self._adv_data[discovery.address] = discovery

    async def discover(
        self, retry: int = DEFAULT_RETRY_COUNT, scan_timeout: int = DEFAULT_SCAN_TIMEOUT
    ) -> dict:
        """Find UberSolar devices."""

        devices = None
        devices = bleak.BleakScanner(
            adapter=self._interface,
            detection_callback=self.detection_callback,
        )

        async with CONNECT_LOCK:
            await devices.start()
            await asyncio.sleep(scan_timeout)
            await devices.stop()

        if devices is None:
            if retry < 1:
                _LOGGER.error(
                    "Scanning for UberSolar devices failed. Stop trying", exc_info=True
                )
                return self._adv_data

            _LOGGER.warning(
                "Error scanning for UberSolar devices. Retrying (remaining: %d)",
                retry,
            )
            await asyncio.sleep(DEFAULT_RETRY_TIMEOUT)
            return await self.discover(retry - 1, scan_timeout)

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
            if adv.data.get("address") == address
        }
