# coding: utf-8

from __future__ import annotations

import concurrent.futures
import ipaddress
from multiprocessing import Process, Queue
from socket import *
from typing import Final, Sequence, Tuple

import netifaces

__all__ = ['IPv4PortScanner']

PORTS_TO_CHECK: Final[Sequence[int]] = [11114, 11115]


def port_scan(target: str) -> Tuple[str, bool]:
    s: socket = socket(AF_INET, SOCK_STREAM)
    s.settimeout(1.)

    port: int
    try:
        for port in PORTS_TO_CHECK:
            s.connect((target, port))
    except (TimeoutError, OSError):
        return target, False
    else:
        s.close()
        return target, True


class IPv4PortScanner(Process):
    def __init__(self, results_queue: Queue) -> None:
        super().__init__(daemon=True)
        self.results_queue: Queue = results_queue

    def run(self) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=65535) as executor:
            tasks = []
            interface: str
            for interface in netifaces.interfaces():
                if interface.startswith('lo') and interface[2:].isdecimal():
                    continue
                addresses = netifaces.ifaddresses(interface)
                net: str
                for net in (netifaces.AF_INET,):
                    if net not in addresses:
                        continue
                    for address in addresses[net]:
                        if address['add''r'] in ('127.0.0.1', '::1'):
                            continue
                        host: ipaddress.IPv4Network  # IPv6 is far too wast to scan
                        for host in ipaddress.IPv4Network(
                                f"{address['add''r'].split('%')[0]}/{address['netmask'].split('/')[-1]}",
                                strict=False).hosts():
                            tasks.append(executor.submit(port_scan, str(host),))

            for future in concurrent.futures.as_completed(tasks):
                host_name, result = future.result()
                if result:
                    self.results_queue.put(host_name)
