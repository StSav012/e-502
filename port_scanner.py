# coding: utf-8

from __future__ import annotations

import concurrent.futures
import ipaddress
from concurrent.futures import Future, ThreadPoolExecutor
from multiprocessing import Process, Queue
from socket import socket, AF_INET, SOCK_STREAM
from typing import Final, Sequence, Tuple, Dict, List

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
    def __init__(self, results_queue: Queue[str]) -> None:
        super().__init__(daemon=True)
        self.results_queue: Queue[str] = results_queue

    def run(self) -> None:
        executor: ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=65535) as executor:
            tasks: List[Future[Tuple[str, bool]]] = []
            interface: str
            for interface in netifaces.interfaces():
                if interface.startswith('lo') and interface[2:].isdecimal():
                    continue
                addresses: Dict[int, List[Dict[str, str]]] = netifaces.ifaddresses(interface)
                net: int
                for net in (netifaces.AF_INET,):
                    if net not in addresses:
                        continue
                    address: Dict[str, str]
                    for address in addresses[net]:
                        if address['add''r'] in ('127.0.0.1', '::1'):
                            continue
                        host: ipaddress.IPv4Address  # IPv6 is far too wast to scan
                        for host in ipaddress.IPv4Network(
                                f"{address['add''r'].split('%')[0]}/{address['netmask'].split('/')[-1]}",
                                strict=False).hosts():
                            tasks.append(executor.submit(port_scan, str(host),))

            future: Future[Tuple[str, bool]]
            for future in concurrent.futures.as_completed(tasks):
                host_name: str
                result: bool
                host_name, result = future.result()
                if result:
                    self.results_queue.put(host_name)
