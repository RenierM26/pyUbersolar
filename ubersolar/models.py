"""Library to handle connection with UberSolar."""
from __future__ import annotations

from dataclasses import dataclass

from bleak.backends.device import BLEDevice


@dataclass
class UberSolarAdvertisement:
    """UberSolar advertisement."""

    address: str
    name: str
    device: BLEDevice
    rssi: int
    active: bool = False
