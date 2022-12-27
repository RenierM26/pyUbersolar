"""Library to handle connection with UberSmart."""
from __future__ import annotations

import logging
from typing import Any

from .device import UberSolarBaseDevice

_LOGGER = logging.getLogger(__name__)


class UberSmart(UberSolarBaseDevice):
    """Representation of a UberSmart Device."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """UberSolar UberSmart constructor."""

        super().__init__(*args, **kwargs)

    async def get_info(self) -> dict[str, Any] | None:
        """Get device statuses."""

        await self._send_command()
        if not self.status_data[self._device.address]:
            _LOGGER.error("%s: Unsuccessful, no result from device", self.name)
            return None

        return self.status_data[self._device.address]

    async def set_pump(self) -> dict[str, Any] | None:
        """Set pump switch."""

        await self._send_command(key="00010002")
        if not self.status_data[self._device.address]:
            _LOGGER.error("%s: Unsuccessful, no result from device", self.name)
            return None

        return
