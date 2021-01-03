#!/usr/bin/env python3

import asyncio
import logging
import sys
from typing import Any, Sequence

import aiohttp
import pysmartthings


API_TOKEN = "3f62cab5-e28e-4a7b-a43f-e17fa85f8563"
LOG = logging.getLogger(__name__)


async def get_devices(api_token: str) -> Sequence[Any]:
    async with aiohttp.ClientSession() as session:
        api = pysmartthings.SmartThings(session, api_token)
        return await api.devices()


def main() -> int:
    loop = asyncio.get_event_loop()
    LOG.info("Lets try get devices and print them")
    devices = loop.run_until_complete(get_devices(API_TOKEN))
    for device in devices:
        print(device)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
