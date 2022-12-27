"""UberSolar get device info test."""
import argparse
import asyncio
import logging

from . import GetUberSolarDevices, UberSmart

logger = logging.getLogger(__name__)


async def main(args: argparse.Namespace):
    """Main program."""

    logger.info("starting scan...")
    device = await GetUberSolarDevices().discover()

    if not device:
        logger.info("Could not find any UberSolar devices in range")
        return

    logger.info("connecting to device and getting info...")

    if args.address:
        uber_smart = UberSmart(device[args.address].device)
        await uber_smart.get_info()
        print(uber_smart.status_data[args.address])

        if args.switch:
            logger.info("setting switches...")
            await uber_smart.toggle_switches_all(args.switch)

        if args.wifiap:
            logger.info("enable ap sta on device...")
            await uber_smart.enable_wifi_ap()

        if args.time:
            logger.info("setting time on device...")
            await uber_smart.set_current_time()

    else:
        for item in device:
            uber_smart = UberSmart(device[item].device)
            await uber_smart.get_info()
            print(uber_smart.status_data)


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

    args = parser.parse_args()

    LOG_LEVEL = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(args))
