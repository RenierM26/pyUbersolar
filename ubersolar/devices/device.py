"""Library to handle connection with UberSolar."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
import time
from typing import Any
from uuid import UUID

from bleak import BleakError
from bleak.backends.device import BLEDevice
from bleak.backends.service import BleakGATTCharacteristic, BleakGATTServiceCollection
from bleak.exc import BleakDBusError
from bleak_retry_connector import (
    BLEAK_RETRY_EXCEPTIONS,
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
)

from ..adv_parsers.ubersmart import process_ubersmart
from ..const import DEFAULT_RETRY_COUNT

_LOGGER = logging.getLogger(__name__)

# How long to hold the connection
# to wait for additional commands for
# disconnecting the device.
DISCONNECT_DELAY = 8.5

# We need to poll to get data
POLL_INTERVAL = 60


class CharacteristicMissingError(Exception):
    """Raised when a characteristic is missing."""


class UberSmartOperationError(Exception):
    """Raised when an operation fails."""


def _uuid(comms_type: str = "service") -> UUID | str:
    """Return UberSolar UUID."""

    _uuid = {
        "tx": "9af90c38",
        "rx": "95b10712",
        "service": "88665b98",
        "FWVersion": "9af90c40",
    }

    if comms_type in _uuid:
        return UUID(f"{_uuid[comms_type]}-0bfb-11ec-9a03-0242ac130003")

    return "Incorrect type, choose between: tx, rx, FWVersion or service"


READ_CHAR_UUID = _uuid(comms_type="tx")
WRITE_CHAR_UUID = _uuid(comms_type="rx")
SERVICE_CHAR_UUID = _uuid()
FW_CHAR_UUID = _uuid(comms_type="FWVersion")


class UberSolarBaseDevice:
    """Base Representation of a UberSolar Device."""

    def __init__(
        self,
        device: BLEDevice,
        interface: int = 0,
        **kwargs: Any,
    ) -> None:
        """Switchbot base class constructor."""
        self._interface = f"hci{interface}"
        self._device = device
        self._retry_count: int = kwargs.pop("retry_count", DEFAULT_RETRY_COUNT)
        self._connect_lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._client: BleakClientWithServiceCache | None = None
        self._read_char: BleakGATTCharacteristic | None = None
        self._write_char: BleakGATTCharacteristic | None = None
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._expected_disconnect = False
        self.loop = asyncio.get_event_loop()
        self._callbacks: list[Callable[[], None]] = []
        self._notify_future: asyncio.Future[bytearray] | None = None
        self.status_data: dict[str, Any] = {}
        self._last_full_update: float = -POLL_INTERVAL

    async def _send_command(
        self, key: str = "", retry: int | None = None
    ) -> bytes | None:
        """Send command to device and read response."""
        if retry is None:
            retry = self._retry_count

        command = bytearray.fromhex(key)
        _LOGGER.debug("%s: Scheduling command %s", self.name, key)
        max_attempts = retry + 1
        if self._operation_lock.locked():
            _LOGGER.debug(
                "%s: Operation already in progress, waiting for it to complete; RSSI: %s",
                self.name,
                self.rssi,
            )
        async with self._operation_lock:
            for attempt in range(max_attempts):
                try:
                    return await self._send_command_locked(command)
                except BleakNotFoundError:
                    _LOGGER.error(
                        "%s: device not found, no longer in range, or poor RSSI: %s",
                        self.name,
                        self.rssi,
                        exc_info=True,
                    )
                    raise
                except CharacteristicMissingError as ex:
                    if attempt == retry:
                        _LOGGER.error(
                            "%s: characteristic missing: %s; Stopping trying; RSSI: %s",
                            self.name,
                            ex,
                            self.rssi,
                            exc_info=True,
                        )
                        raise

                    _LOGGER.debug(
                        "%s: characteristic missing: %s; RSSI: %s",
                        self.name,
                        ex,
                        self.rssi,
                        exc_info=True,
                    )
                except BLEAK_RETRY_EXCEPTIONS:
                    if attempt == retry:
                        _LOGGER.error(
                            "%s: communication failed; Stopping trying; RSSI: %s",
                            self.name,
                            self.rssi,
                            exc_info=True,
                        )
                        raise

                    _LOGGER.debug(
                        "%s: communication failed with:", self.name, exc_info=True
                    )

        raise RuntimeError("Unreachable")

    @property
    def name(self) -> str:
        """Return device name."""
        return f"{self._device.name} ({self._device.address})"

    @property
    def rssi(self) -> int:
        """Return RSSI of device."""
        return self._device.rssi

    async def _ensure_connected(self) -> None:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            _LOGGER.debug(
                "%s: Connection already in progress, waiting for it to complete; RSSI: %s",
                self.name,
                self.rssi,
            )
        if self._client and self._client.is_connected:
            self._reset_disconnect_timer()
            return
        async with self._connect_lock:
            # Check again while holding the lock
            if self._client and self._client.is_connected:
                self._reset_disconnect_timer()
                return
            _LOGGER.debug("%s: Connecting; RSSI: %s", self.name, self.rssi)
            client: BleakClientWithServiceCache = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self.name,
                self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: self._device,
            )
            _LOGGER.debug("%s: Connected; RSSI: %s", self.name, self.rssi)

            try:
                self._resolve_characteristics(client.services)
            except CharacteristicMissingError as ex:
                _LOGGER.debug(
                    "%s: characteristic missing, clearing cache: %s; RSSI: %s",
                    self.name,
                    ex,
                    self.rssi,
                    exc_info=True,
                )
                await client.clear_cache()
                await self._execute_forced_disconnect()
                raise

            self._client = client
            self._reset_disconnect_timer()
            await self._start_notify()

    def _resolve_characteristics(self, services: BleakGATTServiceCollection) -> None:
        """Resolve characteristics."""
        self._read_char = services.get_characteristic(READ_CHAR_UUID)
        if not self._read_char:
            raise CharacteristicMissingError(READ_CHAR_UUID)
        self._write_char = services.get_characteristic(WRITE_CHAR_UUID)
        if not self._write_char:
            raise CharacteristicMissingError(WRITE_CHAR_UUID)

    def _reset_disconnect_timer(self) -> None:
        """Reset disconnect timer."""
        self._cancel_disconnect_timer()
        self._expected_disconnect = False
        self._disconnect_timer = self.loop.call_later(
            DISCONNECT_DELAY, self._disconnect_from_timer
        )

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Disconnected callback."""
        if self._expected_disconnect:
            _LOGGER.debug(
                "%s: Disconnected from device; RSSI: %s", self.name, self.rssi
            )
            return
        _LOGGER.warning(
            "%s: Device unexpectedly disconnected; RSSI: %s",
            self.name,
            self.rssi,
        )

    def _disconnect_from_timer(self) -> None:
        """Disconnect from device."""
        if self._operation_lock.locked() and self._client.is_connected:
            _LOGGER.debug(
                "%s: Operation in progress, resetting disconnect timer; RSSI: %s",
                self.name,
                self.rssi,
            )
            self._reset_disconnect_timer()
            return
        self._cancel_disconnect_timer()
        asyncio.create_task(self._execute_timed_disconnect())

    def _cancel_disconnect_timer(self) -> None:
        """Cancel disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    async def _execute_forced_disconnect(self) -> None:
        """Execute forced disconnection."""
        self._cancel_disconnect_timer()
        _LOGGER.debug(
            "%s: Executing forced disconnect",
            self.name,
        )
        await self._execute_disconnect()

    async def _execute_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        _LOGGER.debug(
            "%s: Executing timed disconnect after timeout of %s",
            self.name,
            DISCONNECT_DELAY,
        )
        await self._execute_disconnect()

    async def _execute_disconnect(self) -> None:
        """Execute disconnection."""
        async with self._connect_lock:
            if self._disconnect_timer:  # If the timer was reset, don't disconnect
                return
            client = self._client
            self._expected_disconnect = True
            self._client = None
            self._read_char = None
            self._write_char = None
            if client and client.is_connected:
                _LOGGER.debug("%s: Disconnecting", self.name)
                await client.disconnect()
                _LOGGER.debug("%s: Disconnect completed", self.name)

    async def _send_command_locked(self, command: bytes) -> bytes:
        """Send command to device and read response."""
        await self._ensure_connected()
        if command != b"":
            try:
                return await self._execute_command_locked(command)
            except BleakDBusError as ex:
                # Disconnect so we can reset state and try again
                await asyncio.sleep(0.25)
                _LOGGER.debug(
                    "%s: RSSI: %s; Backing off %ss; Disconnecting due to error: %s",
                    self.name,
                    self.rssi,
                    0.25,
                    ex,
                )
                await self._execute_forced_disconnect()
                raise
            except BleakError as ex:
                # Disconnect so we can reset state and try again
                _LOGGER.debug(
                    "%s: RSSI: %s; Disconnecting due to error: %s",
                    self.name,
                    self.rssi,
                    ex,
                )
                await self._execute_forced_disconnect()
                raise

    def _notification_handler(self, _sender: int, data: bytearray) -> None:
        """Handle notification responses."""
        _LOGGER.debug("%s: Received notification: %s", self.name, data)
        self.status_data[self._device.address].update(process_ubersmart(data))

    async def _start_notify(self) -> None:
        """Start notification."""
        _LOGGER.debug("%s: Subscribe to notifications; RSSI: %s", self.name, self.rssi)

        self.status_data[self._device.address] = {}
        await self._client.start_notify(self._read_char, self._notification_handler)
        await asyncio.sleep(3)

    async def _execute_command_locked(self, command: bytes) -> None:
        """Execute command and read response."""
        assert self._client is not None
        assert self._read_char is not None
        assert self._write_char is not None

        _LOGGER.debug("%s: Sending command: %s", self.name, command.hex())
        await self._client.write_gatt_char(self._write_char, command, False)

        return

    def get_address(self) -> str:
        """Return address of device."""
        return self._device.address

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe to device notifications."""
        self._callbacks.append(callback)

        def _unsub() -> None:
            """Unsubscribe from device notifications."""
            self._callbacks.remove(callback)

        return _unsub

    async def update(self) -> bool:
        """Get device updates."""
        await self.get_info()
        self._last_full_update = time.monotonic()
        self._fire_callbacks()
        return True

    def poll_needed(self, seconds_since_last_poll: float | None) -> bool:
        """Return if device needs polling."""
        if (
            seconds_since_last_poll is not None
            and seconds_since_last_poll < POLL_INTERVAL
        ):
            return False
        time_since_last_full_update = time.monotonic() - self._last_full_update
        if time_since_last_full_update < POLL_INTERVAL:
            return False
        return True

    def _fire_callbacks(self) -> None:
        """Fire callbacks."""
        _LOGGER.debug("%s: Fire callbacks", self.name)
        for callback in self._callbacks:
            callback()

    async def get_info(self) -> dict[str, Any] | None:
        """Get device statuses."""

        await self._send_command()
        if not self.status_data[self._device.address]:
            _LOGGER.error("%s: Unsuccessful, no result from device", self.name)

        return self.status_data[self._device.address]

    def _check_command_result(
        self, result: bytes | None, index: int, values: set[int]
    ) -> bool:
        """Check command result."""
        if not result or len(result) - 1 < index:
            result_hex = result.hex() if result else "None"
            raise UberSmartOperationError(
                f"{self.name}: Sending command failed (result={result_hex} index={index} expected={values} rssi={self.rssi})"
            )
        return result[index] in values
