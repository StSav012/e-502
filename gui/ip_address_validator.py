# coding: utf-8

from __future__ import annotations

from typing import Tuple

import pyqtgraph as pg  # type: ignore

if pg.Qt.QT_LIB == pg.Qt.PYSIDE6:
    from PySide6.QtGui import QValidator  # type: ignore
elif pg.Qt.QT_LIB == pg.Qt.PYQT5:
    from PyQt5.QtGui import QValidator  # type: ignore
elif pg.Qt.QT_LIB == pg.Qt.PYSIDE2:
    from PySide2.QtGui import QValidator  # type: ignore
else:
    raise ImportError('PySide6, or PyQt5, or PySide2, is required. PyQt6 is not supported.')


class IPAddressValidator(QValidator):
    def validate(self, text: str, text_length: int) -> Tuple[QValidator.State, str, int]:
        if not text:
            return QValidator.State.Invalid, text, 0
        import ipaddress
        try:
            ipaddress.ip_address(text)
        except ValueError:
            if '.' in text and text.count('.') <= 3 and set(text).issubset(set('0123456789.')):
                return QValidator.State.Intermediate, text, 0
            if ':' in text and set(text.casefold()).issubset(set('0123456789a''bc''def:')):
                return QValidator.State.Intermediate, text, 0
            return QValidator.State.Invalid, text, 0
        else:
            return QValidator.State.Acceptable, text, 0
