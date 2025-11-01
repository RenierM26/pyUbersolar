"""Library to handle connection with UberSolar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from bleak.backends.device import BLEDevice


@dataclass
class UberSolarAdvertisement:
    """UberSolar advertisement."""

    address: str
    name: str
    device: BLEDevice
    rssi: int
    active: bool = False


class UberSmartStatus(TypedDict, total=False):
    """Represents the known state values for a UberSmart device."""

    fWaterTemperature: float
    fManifoldTemperature: float
    fStoredWater: float
    bElementOn: int
    bPumpOn: int
    bHolidayMode: int
    eSolenoidMode: int
    fSolenoidState: float
    AllSwitches: bytearray
    lluTime: str
    fHours: float
    wLux: int
    wRSSI: int
    fPanelVoltage: float
    fChipTemp: float
    fWaterLevel: float
    fTankSize: float
    bPanelFaultCode: int
    bElementFaultCode: int
    bPumpFultCode: int
    bSolenoidFaultCode: int
