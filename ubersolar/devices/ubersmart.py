"""Library to handle connection with UberSmart."""
from __future__ import annotations

import logging
import struct
import time
from typing import Any

from .device import UberSolarBaseDevice

_LOGGER = logging.getLogger(__name__)


class UberSmart(UberSolarBaseDevice):
    """Representation of a UberSmart Device."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """UberSolar UberSmart constructor."""

        super().__init__(*args, **kwargs)

    async def toggle_switches_all(self, switches: str) -> None:
        """Set pump switch."""

        # 1st byte is message id, use 06 to toggle switches.
        # need to send  all switches.
        # elementToggle, pumpToggle, holidayModeToggle, solenoidMode = 0 - off, 1 - on, 2 - auto
        # example 0600000002
        if not len(switches) == 8:
            _LOGGER.error("Switch length has to be 8")

        await self._send_command(key=f"06{switches}")
        _LOGGER.info("%s: Toggle switches", self.name)

    async def enable_wifi_ap(self) -> None:
        """Enable Wifi ap mode on device."""
        # intended for firmware update but who knows.
        await self._send_command(key="14")
        _LOGGER.info("%s: Enable Wifi AP on device", self.name)

    async def set_current_time(self) -> None:
        """Set current datetime on device."""

        current_time = int(time.time())
        ct_to_bytearray = bytearray(struct.pack("<Qxxxx", current_time))
        ct_to_bytearray[9] = 2  # add utc offset on byte 9

        await self._send_command(key=f"09{ct_to_bytearray.hex()}")
        _LOGGER.info("%s: Send current time to device", self.name)
