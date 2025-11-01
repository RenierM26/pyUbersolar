"""UberSolar get device info test."""

import argparse
import asyncio
import logging

from .devices.ubersmart import UberSmart
from .discovery import GetUberSolarDevices

logger = logging.getLogger(__name__)


async def main(cli_args: argparse.Namespace) -> None:
    """Main program."""

    logger.info("starting scan...")
    devices = await GetUberSolarDevices().discover()

    if not devices:
        logger.info("Could not find any UberSolar devices in range")
        return

    logger.info("connecting to device and getting info...")

    if cli_args.address:
        uber_smart = UberSmart(devices[cli_args.address].device)
        await uber_smart.get_info()
        logger.info("Status data: %s", uber_smart.status_data[cli_args.address])

        if cli_args.switch:
            logger.info("setting switches...")
            await uber_smart.toggle_switches_all(cli_args.switch)

        if cli_args.wifiap:
            logger.info("enable ap sta on device...")
            await uber_smart.enable_wifi_ap()

        if cli_args.time:
            logger.info("setting time on device...")
            await uber_smart.set_current_time()

    else:
        for item in devices:
            uber_smart = UberSmart(devices[item].device)
            await uber_smart.get_info()
            logger.info("Status data for %s: %s", item, uber_smart.status_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--address",
        metavar="<address>",
        help="the address of the bluetooth device to connect to",
    )

    # elementToggle, pumpToggle, holidayModeToggle, solenoidMode = 0 - off, 1 - on, 2 - auto
    parser.add_argument(
        "--switch",
        metavar="<switch>",
        help="Set switches on device",
    )
    parser.add_argument(
        "--wifiap",
        action="store_true",
        help="enable wifiap on device",
    )
    parser.add_argument(
        "--time",
        action="store_true",
        help="Update device date and time",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )

    parsed_args = parser.parse_args()

    LOG_LEVEL = logging.DEBUG if parsed_args.debug else logging.INFO
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(parsed_args))
