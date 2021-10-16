# coding: utf-8

from __future__ import annotations

from multiprocessing import Queue
from queue import Empty
from typing import Optional

from gui.pg_qt import *
from port_scanner import IPv4PortScanner

__all__ = ['IPAddressDialog']


class IPAddressDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout: QVBoxLayout = QVBoxLayout(self)
        self.list_addresses: QListWidget = QListWidget(self)
        layout.addWidget(self.list_addresses)
        self.timer: QTimer = QTimer(self)

        self.results_queue: Queue = Queue()
        self.scanner: IPv4PortScanner = IPv4PortScanner(self.results_queue)

        self.timer.setInterval(100)
        self.timer.timeout.connect(self.on_timeout)
        self.list_addresses.doubleClicked.connect(self.on_double_click)

    def __del__(self) -> None:
        self.timer.stop()
        if self.scanner.is_alive():
            self.scanner.kill()

    def exec_(self) -> int:
        return self.exec()

    def exec(self) -> int:
        self.scanner.start()
        self.timer.start()
        if hasattr(super(), 'exec'):
            return super().exec()
        elif hasattr(super(), 'exec_'):
            return super().exec_()
        else:
            raise AttributeError('No `exec` method found.')

    @property
    def address(self) -> str:
        if self.list_addresses.currentItem() is None:
            return ''
        return self.list_addresses.currentItem().text()

    def on_timeout(self) -> None:
        while not self.results_queue.empty():
            try:
                host: str = self.results_queue.get(block=True, timeout=0.01)
            except Empty:
                pass  # wait more for data
            else:
                self.list_addresses.addItem(host)

    def on_double_click(self, _: QModelIndex) -> None:
        self.accept()
