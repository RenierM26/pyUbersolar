"""Library to handle connection with UberSmart."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import struct
from typing import Any

from .device import UberSolarBaseDevice, update_after_operation

_LOGGER = logging.getLogger(__name__)


class UberSmart(UberSolarBaseDevice):
    """Representation of a UberSmart Device."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """UberSolar UberSmart constructor."""

        super().__init__(*args, **kwargs)

    @update_after_operation
    async def toggle_switches_all(self, switches: str) -> None:
        """Set all switches from hex string."""

        # 1st byte is message id, use 06 to toggle switches.
        # need to send  all switches.
        # elementToggle, pumpToggle, holidayModeToggle, solenoidMode = 0 - off, 1 - on, 2 - auto
        # example 0600000002
        if len(switches) != 8:
            _LOGGER.error("Switch length has to be 8")

        await self._send_command(key=f"06{switches}")
        _LOGGER.info("%s: Toggle switches", self.name)

    async def enable_wifi_ap(self) -> None:
        """Enable Wifi ap mode on device."""
        # intended for firmware update but who knows.
        await self._send_command(key="14")
        _LOGGER.info("%s: Enable Wifi AP on device", self.name)

    def _build_time_payload(self, value: datetime) -> bytearray:
        """Build the payload used to set device time."""
        if value.tzinfo is None:
            _LOGGER.warning("%s: naive datetime provided; assuming UTC", self.name)
            value = value.replace(tzinfo=UTC)

        offset = value.utcoffset() or timedelta()
        offset_seconds = int(offset.total_seconds())
        offset_hours = int(offset_seconds / 3600)
        if offset_seconds % 3600 != 0:
            _LOGGER.warning(
                "%s: timezone offset %s is not an integer hour; truncating to %s",
                self.name,
                offset,
                offset_hours,
            )
        if not -128 <= offset_hours <= 127:
            _LOGGER.warning(
                "%s: timezone offset %s out of supported range; clamping",
                self.name,
                offset_hours,
            )
            offset_hours = max(-128, min(127, offset_hours))

        payload = bytearray(struct.pack("<Qxxxx", int(value.timestamp())))
        payload[9] = offset_hours & 0xFF
        return payload

    async def _send_time(self, value: datetime) -> None:
        payload = self._build_time_payload(value)
        await self._send_command(key=f"09{payload.hex()}")
        _LOGGER.info("%s: Send time %s to device", self.name, value.isoformat())

    @update_after_operation
    async def set_time(self, value: datetime) -> None:
        """Set provided datetime on device."""
        await self._send_time(value)

    @update_after_operation
    async def set_current_time(self) -> None:
        """Set current datetime on device."""
        await self._send_time(datetime.now(UTC).astimezone())

    @update_after_operation
    async def turn_on_element(self) -> None:
        """Turn element switch on."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[1] = 1
        current_switches[2] = 0  # Pump can't be on as well.

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Element On", self.name)

    @update_after_operation
    async def turn_off_element(self) -> None:
        """Turn element switch off."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[1] = 0

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Element Off", self.name)

    @update_after_operation
    async def turn_on_pump(self) -> None:
        """Turn pump switch on."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[1] = 0  # Pump and element can't be on at same time.
        current_switches[2] = 1

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Pump On", self.name)

    @update_after_operation
    async def turn_off_pump(self) -> None:
        """Turn pump switch off."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[2] = 0

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Pump Off", self.name)

    @update_after_operation
    async def turn_on_holiday(self) -> None:
        """Turn holiday switch on."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[3] = 1

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Holiday On", self.name)

    @update_after_operation
    async def turn_off_holiday(self) -> None:
        """Turn holiday switch off."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[3] = 0

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Holiday Off", self.name)

    @update_after_operation
    async def set_solinoid_off(self) -> None:
        """Turn Solinoid off."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[4] = 0

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Solinoid Off", self.name)

    @update_after_operation
    async def set_solinoid_on(self) -> None:
        """Turn Solinoid on."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[4] = 1

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Solinoid On", self.name)

    @update_after_operation
    async def set_solinoid_auto(self) -> None:
        """Set Solinoid to Auto."""

        if not self.status_data:
            await self.update()

        current_switches = self.status_data[self._device.address]["AllSwitches"]

        if len(current_switches) != 5:
            _LOGGER.error("Switch length has to be 5 bytes")

        current_switches[0] = 6
        current_switches[4] = 2

        await self._send_command(key=current_switches.hex())
        _LOGGER.info("%s: Turn Solinoid to Auto", self.name)
