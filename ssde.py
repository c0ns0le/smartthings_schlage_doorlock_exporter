#!/usr/bin/env python3

import argparse
import asyncio
import aiohttp
import logging
import sys
import time
from collections import defaultdict
from os import environ
from typing import Dict, Generator, List, Optional

import pysmartthings
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server


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

    async def get_lock_stats(self) -> Dict[str, float]:
        lock_device: Optional[pysmartthings.device.DeviceEntity] = None
        stats: Dict[str, float] = defaultdict(float)

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
            LOG.error(f"Unable to find Lock Device {self.device_id}")
            return {}

        for name, status in lock_device.status.attributes.items():
            if name not in self.ATTRIBUTE_SELECT_LIST:
                continue

            if name == "lock":
                stats[name] = self.LockStatus[status.value]
            elif name == "lockCodes":
                codes = eval(status.value)
                stats[name] = float(len(codes))
            else:
                stats[name] = float(status.value)

        return stats


class PrometheusCollector:
    """Prometheus Collector class to get SmartLock status and convert to
    Guages via HTTP server."""

    labels: List[str] = ["device_name"]

    help_test = {
        "battery": "Battery Level %",
        "codeLength": "Length of codes",
        "lock": "Is door locked? (boolean)",
        "lockCodes": "Number of lock codes set",
        "maxCodes": "Max number of codes lock can handle",
    }

    def __init__(
        self,
        device_name: str,
        lock: SmartthingsSchlageDoorLock,
        key_prefix="schlagedoorlock",
    ) -> None:
        self.device_name = device_name
        self.lock = lock
        self.key_prefix = key_prefix

    def _handle_counter(self, category: str, value: float) -> GaugeMetricFamily:
        normalized_category = category.replace(" ", "_")
        key = f"{self.key_prefix}_{normalized_category}"
        g = GaugeMetricFamily(
            key,
            self.help_test.get(normalized_category, "Schlage Metric"),
            labels=self.labels,
        )
        g.add_metric([self.key_prefix], value)
        return g

    def collect(self) -> Generator[GaugeMetricFamily, None, None]:
        start_time = time.time()
        LOG.info("Collection started")

        stats = asyncio.run(self.lock.get_lock_stats())
        if not stats:
            LOG.error("Problem with collecting lock stats")
            return

        for category, value in stats.items():
            yield self._handle_counter(category, value)

        run_time = time.time() - start_time
        LOG.info(f"Collection finished in {run_time}s")


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
    parser.add_argument(
        "-n",
        "--device-name",
        default=environ.get("SMARTTINGS_DEVICE_NAME", ""),
        help="Smartthing API Device Name used for guage label",
    )
    parser.add_argument(
        "-p",
        "--port",
        default=1338,
        type=int,
        help="Prometheus Exporter TCP Port",
    )
    parser.add_argument(
        "-P",
        "--print",
        action="store_true",
        help="Print stats rather than run HTTP Server",
    )
    return parser


def serve(args: argparse.Namespace, lock: SmartthingsSchlageDoorLock) -> int:
    start_http_server(args.port)
    REGISTRY.register(PrometheusCollector(args.device_name, lock))
    LOG.info(f"Smartthings Schlege Door Lock Exporter - listening on {args.port}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        LOG.info("Shutting down ...")
    return 0


def _handle_debug(debug: bool) -> bool:
    """Turn on debugging if asked otherwise INFO default"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)",
        level=log_level,
    )
    return debug


def main() -> int:
    parser = args_setup()
    args = parser.parse_args()
    _handle_debug(args.debug)

    if not args.api_token or not args.device_id or not args.device_name:
        LOG.error("Please specify an API Token, Device ID + Device Name")
        return 1

    lock = SmartthingsSchlageDoorLock(args.api_token, args.device_id)
    if args.print:
        print(asyncio.run(lock.get_lock_stats()))
        return 0

    return serve(args, lock)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
