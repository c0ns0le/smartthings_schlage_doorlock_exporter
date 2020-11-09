#!/usr/bin/env python3

"""
checkInterval status(value=3600, unit='s', data={'protocol': 'zwave', 'hubHardwareId': '0020', 'offlinePingable': '1', 'deviceScheme': 'TRACKED'})
healthStatus status(value=None, unit=None, data={})
DeviceWatch-Enroll status(value=None, unit=None, data=None)
DeviceWatch-DeviceStatus status(value=None, unit=None, data={})
lock status(value='unlocked', unit=None, data=None)
battery status(value=47, unit='%', data=None)
codeLength status(value=4, unit=None, data=None)
maxCodes status(value=30, unit=None, data=None)
maxCodeLength status(value=None, unit=None, data=None)
codeChanged status(value='8 unset', unit=None, data=None)
minCodeLength status(value=None, unit=None, data=None)
codeReport status(value=[3], unit=None, data=None)
scanCodes status(value='Complete', unit=None, data=None)
lockCodes status(value='{"1":"Code 1","2":"Code 2","3":"Code 3"}', unit=None, data=None)
"""

import asyncio
import aiohttp
import logging
import sys
from collections import defaultdict
from os import environ
from typing import Optional

import pysmartthings


API_TOKEN = environ["SMARTTHINGS_API_TOKEN"]
LOCK_DEVICE_ID = environ["SMARTTINGS_DEVICE_ID"]
LOG = logging.getLogger(__name__)


class SmartthingsSchlageDoorLock:
    ATTRIBUTE_SELECT_LIST = ("battery", "codeLength", "lock", "lockCodes", "maxCodes")
    LockStatus = {
        "unlocked": 0.0,
        "locked": 1.0,
    }

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        self.stats = defaultdict(float)

    async def get_lock_stats(self) -> bool:
        lock_device: Optional[pysmartthings.device.DeviceEntity] = None

        async with aiohttp.ClientSession() as session:
            api = pysmartthings.SmartThings(session, API_TOKEN)
            devices = await api.devices()

            for device in devices:
                if device.device_id != self.device_id:
                    continue

                await device.status.refresh()
                lock_device = device
                break

        if not lock_device:
            LOG.error(f"Unable to find Lock Device {LOCK_DEVICE_ID}")
            return False

        for name, status in lock_device.status.attributes.items():
            if name not in self.ATTRIBUTE_SELECT_LIST:
                continue

            if name == "lock":
                self.stats[name] = self.LockStatus[status.value]
            elif name == "lockCodes":
                codes = eval(status.value)
                self.stats[name] = float(len(codes))
            else:
                self.stats[name] = float(status.value)

        return True


def main() -> int:
    lock = SmartthingsSchlageDoorLock(LOCK_DEVICE_ID)
    asyncio.run(lock.get_lock_stats())
    print(lock.stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
