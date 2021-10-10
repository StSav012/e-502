# coding: utf-8

from __future__ import annotations

from typing import Optional, Union

from gui.pg_qt import *

__all__ = ['ToggleButton']


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
