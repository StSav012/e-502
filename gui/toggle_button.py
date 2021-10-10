# coding: utf-8

from __future__ import annotations

from typing import Optional, Union

import pyqtgraph as pg  # type: ignore

if pg.Qt.QT_LIB == pg.Qt.PYSIDE6:
    from PySide6.QtCore import Qt  # type: ignore
    from PySide6.QtGui import QColor, QPalette, QPaintEvent  # type: ignore
    from PySide6.QtWidgets import QPushButton, QWidget  # type: ignore
elif pg.Qt.QT_LIB == pg.Qt.PYQT5:
    from PyQt5.QtCore import Qt  # type: ignore
    from PyQt5.QtGui import QColor, QPalette, QPaintEvent  # type: ignore
    from PyQt5.QtWidgets import QPushButton, QWidget  # type: ignore
elif pg.Qt.QT_LIB == pg.Qt.PYSIDE2:
    from PySide2.QtCore import Qt  # type: ignore
    from PySide2.QtGui import QColor, QPalette, QPaintEvent  # type: ignore
    from PySide2.QtWidgets import QPushButton, QWidget  # type: ignore
else:
    raise ImportError('PySide6, or PyQt5, or PySide2, is required. PyQt6 is not supported.')


class ToggleButton(QPushButton):
    def __init__(self, color: Union[Qt.GlobalColor, QColor],
                 title: str = '', parent: Optional[QWidget] = None) -> None:
        if title:
            super().__init__(title, parent)
        else:
            super().__init__(parent)

        self._color: QColor = QColor(color)
        self._orig_palette: QPalette = self.palette()

        self.setCheckable(True)
        self.setAutoFillBackground(True)

    def paintEvent(self, ev: QPaintEvent):
        if self.isChecked():
            pal: QPalette = self.palette()
            color: QColor
            color = self._color
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, color)
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                         QColor('white' if color.lightnessF() < 0.5 else 'black'))
            color = QColor.fromHslF(self._color.hueF(),
                                    self._color.saturationF(),
                                    self._color.lightnessF() * 0.5)
            pal.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Button, color)
            pal.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ButtonText,
                         QColor('white' if color.lightnessF() < 0.5 else 'black'))
            self.setPalette(pal)
        else:
            self.setPalette(self._orig_palette)
        super().paintEvent(ev)
