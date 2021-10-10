# coding: utf-8

from __future__ import annotations

from typing import List, Optional, Iterator

import pyqtgraph as pg  # type: ignore

from gui.pg_qt import *
from gui.toggle_button import ToggleButton

__all__ = ['DigitalLines']


class DigitalLines(QGroupBox):
    def __init__(self, title: str = '', parent: Optional[QWidget] = None) -> None:
        if title:
            super().__init__(title, parent)
        else:
            super().__init__(parent)
        layout: QHBoxLayout = QHBoxLayout(self)
        self.buttons: List[QPushButton] = []
        i: int
        for i in range(16):
            self.buttons.append(ToggleButton(Qt.GlobalColor.darkGreen, str(i + 1), self))
            self.buttons[-1].setFixedWidth(self.buttons[-1].minimumSizeHint().height())
            layout.addWidget(self.buttons[-1])

    def __len__(self) -> int:
        return len(self.buttons)

    def __getitem__(self, index: int) -> bool:
        if 1 <= index <= len(self):
            return self.buttons[index - 1].isChecked()
        else:
            raise IndexError

    def __setitem__(self, index: int, pushed: bool) -> None:
        if 1 <= index <= len(self):
            return self.buttons[index - 1].setChecked(pushed)
        else:
            raise IndexError

    def __iter__(self) -> Iterator[bool]:
        b: QPushButton
        for b in self.buttons:
            yield b.isChecked()
