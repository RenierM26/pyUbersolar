"""Library to decode UberSmart Response."""
from __future__ import annotations

import datetime
import struct
from typing import Any


def process_ubersmart(data: bytearray) -> dict[str, Any]:
    """Process UberSmart data."""

    if data[0] == 1:
        return {
            "fWaterTemperature": round(struct.unpack("<f", data[1:5])[0], 2),
            "fManifoldTemperature": round(struct.unpack("<f", data[5:9])[0], 2),
            "fStoredWater": round(struct.unpack("<f", data[9:13])[0], 2),
        }

    if data[0] == 2:
        return {
            "bElementOn": data[1],
            "bPumpOn": data[2],
            "bHolidayMode": data[3],
            "eSolenoidMode": data[4],
            "fSolenoidState": round(struct.unpack("<f", data[5:9])[0], 2),
            "AllSwitches": data[:5],
        }

    if data[0] == 3:
        _llu_time = struct.unpack("<Q", data[1:9])[0]
        return {
            "lluTime": datetime.datetime.fromtimestamp(_llu_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "fHours": round(struct.unpack("<f", data[9:13])[0], 2),  # Time on
            "wLux": struct.unpack("<H", data[13:15])[0],
        }

    if data[0] == 4:
        return {
            "wRSSI": struct.unpack("<h", data[1:3])[0],
            "fPanelVoltage": round(struct.unpack("<f", data[3:7])[0], 2),
            "fChipTemp": round(struct.unpack("<f", data[7:11])[0], 2),
            "fWaterLevel": round(struct.unpack("<f", data[11:15])[0], 2),
            "fTankSize": round(struct.unpack("<f", data[15:19])[0], 2),
        }

    if data[0] == 5:
        return {
            "bPanelFaultCode": struct.unpack("<B", data[1:2])[0],
            "bElementFaultCode": struct.unpack("<B", data[2:3])[0],
            "bPumpFultCode": struct.unpack("<B", data[3:4])[0],
            "bSolenoidFaultCode": struct.unpack("<B", data[4:5])[0],
        }

    return {}
