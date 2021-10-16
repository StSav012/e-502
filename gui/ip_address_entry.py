# coding: utf-8

from __future__ import annotations

from multiprocessing import Queue
from typing import Optional

from gui.ip_address_dialog import IPAddressDialog
from gui.ip_address_validator import IPAddressValidator
from gui.pg_qt import *

__all__ = ['IPAddressEntry']


class IPAddressEntry(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout: QHBoxLayout = QHBoxLayout(self)
        self.text_ip_address: QLineEdit = QLineEdit(self)
        layout.addWidget(self.text_ip_address, 1)
        self.browse_button: QToolButton = QToolButton(self)
        layout.addWidget(self.browse_button, 0)

        self.browse_button.setText(self.tr('...'))
        self.browse_button.setToolTip(self.tr('Browse...'))
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_ip_address.setValidator(IPAddressValidator())
        self.browse_button.clicked.connect(self.browse)

        self.results_queue: Queue = Queue()

    @property
    def text(self) -> str:
        return self.text_ip_address.text()

    @text.setter
    def text(self, new_value: str) -> None:
        self.text_ip_address.setText(str(new_value))

    def browse(self) -> None:
        dialog: IPAddressDialog = IPAddressDialog(self)
        if dialog.exec() == QDialog.DialogCode.Rejected:
            return
        ip: str = dialog.address
        if ip:
            self.text_ip_address.setText(ip)
