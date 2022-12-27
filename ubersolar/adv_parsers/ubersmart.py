"""Library to decode UberSmart Response."""
from __future__ import annotations

import datetime
import struct
from typing import Any


def process_ubersmart(data: bytearray) -> dict[str, Any]:
    """Process UberSmart data."""

    if data[0] == 1:
        return {
            "temps": {
                "fWaterTemperature": struct.unpack("<f", data[1:5])[0],
                "fManifoldTemperature": struct.unpack("<f", data[5:9])[0],
                "fStoredWater": struct.unpack("<f", data[9:13])[0],
            }
        }

    if data[0] == 2:
        return {
            "switches": {
                "bElementOn": data[1],
                "bPumpOn": data[2],
                "bHolidayMode": data[3],
                "eSolenoidMode": data[4],
                "fSolenoidState": struct.unpack("<f", data[5:9])[0],
            }
        }

    if data[0] == 3:
        _llu_time = struct.unpack("<Q", data[1:9])[0]
        return {
            "diag1": {
                "lluTime": datetime.datetime.fromtimestamp(_llu_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "fHours": struct.unpack("<f", data[9:13])[0],  # Time on
                "wLux": struct.unpack("<H", data[13:15])[0],
            }
        }

    if data[0] == 4:
        return {
            "diag2": {
                "wRSSI": struct.unpack("<h", data[1:3])[0],
                "fPanelVoltage": struct.unpack("<f", data[3:7])[0],
                "fChipTemp": struct.unpack("<f", data[7:11])[0],
                "fWaterLevel": struct.unpack("<f", data[11:15])[0],
                "fTankSize": struct.unpack("<f", data[15:19])[0],
            }
        }

    if data[0] == 5:
        return {
            "FaultCodes": {
                "bPanelFaultCode": struct.unpack("<B", data[1:2])[0],
                "bElementFaultCode": struct.unpack("<B", data[2:3])[0],
                "bPumpFultCode": struct.unpack("<B", data[3:4])[0],
                "bSolenoidFaultCode": struct.unpack("<B", data[4:5])[0],
            }
        }

    return {}
