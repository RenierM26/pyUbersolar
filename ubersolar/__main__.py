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

    logger.info("connecting to device...")
    uber_smart = UberSmart(device)
    await uber_smart.get_info()
    print(uber_smart.status_data)


if __name__ == "__main__":
    asyncio.run(main())
