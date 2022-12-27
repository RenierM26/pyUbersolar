"""UberSolar get device info test."""
import logging
import asyncio

from . import UberSmart, GetUberSolarDevices

logger = logging.getLogger(__name__)


async def main():
    """Main program."""

    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    logger.info("starting scan...")
    device = GetUberSolarDevices()
    await device.discover()

    if device._adv_data:
        logger.info("connecting to device...")
        for item in device._adv_data:
            uber_smart = UberSmart(device._adv_data[item].device)
            await uber_smart.get_info()
            print(uber_smart.status_data)

    logger.info("Could not find any UberSolar devices in range")


if __name__ == "__main__":
    asyncio.run(main())
