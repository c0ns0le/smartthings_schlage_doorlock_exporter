#!/usr/bin/env python3

import argparse
import asyncio
import aiohttp
import logging
import sys
from collections import defaultdict
from os import environ
from typing import Optional

import pysmartthings


LOG = logging.getLogger(__name__)


class SmartthingsSchlageDoorLock:
    ATTRIBUTE_SELECT_LIST = ("battery", "codeLength", "lock", "lockCodes", "maxCodes")
    LockStatus = {
        "unlocked": 0.0,
        "locked": 1.0,
    }

    def __init__(self, api_token: str, device_id: str) -> None:
        self.api_token = api_token
        self.device_id = device_id
        self.stats = defaultdict(float)

    async def get_lock_stats(self) -> bool:
        lock_device: Optional[pysmartthings.device.DeviceEntity] = None

        async with aiohttp.ClientSession() as session:
            api = pysmartthings.SmartThings(session, self.api_token)
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


def args_setup() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--api-token",
        default=environ.get("SMARTTHINGS_API_TOKEN", ""),
        help="Smartthing API token",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Verbose debug output"
    )
    parser.add_argument(
        "-D",
        "--device-id",
        default=environ.get("SMARTTINGS_DEVICE_ID", ""),
        help="Smartthing API Device ID",
    )
    return parser


def main() -> int:
    parser = args_setup()
    args = parser.parse_args()

    lock = SmartthingsSchlageDoorLock(args.api_token, args.device_id)
    asyncio.run(lock.get_lock_stats())
    print(lock.stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
