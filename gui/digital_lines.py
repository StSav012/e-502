# coding: utf-8

from __future__ import annotations

from typing import List, Optional, Iterator

from gui.pg_qt import *

__all__ = ['DigitalLines']


class DigitalLines(QGroupBox):
    def __init__(self, title: str = '', parent: Optional[QWidget] = None) -> None:
        if title:
            super().__init__(title, parent)
        else:
            super().__init__(parent)
        layout: QFormLayout = QFormLayout(self)
        self.buttons: List[bool] = [False] * 8

        self.setCheckable(True)
        self.toggled.connect(self.on_toggled)

        self.more_emitter_voltage: QCheckBox = QCheckBox(self.tr('Increase emitter voltage'), self)
        layout.addWidget(self.more_emitter_voltage)
        self.more_emitter_voltage.toggled.connect(self.on_more_emitter_voltage_toggled)

        self.combo_amplification: QComboBox = QComboBox(self)
        self.combo_amplification.addItems(('×1', '×2', '×4', '×8'))
        layout.addRow(self.tr('Amplification:'), self.combo_amplification)
        self.combo_amplification.currentIndexChanged.connect(self.on_amplification_changed)

        self.combo_pulse_duration: QComboBox = QComboBox(self)
        self.combo_pulse_duration.addItems(('5 us', '10 us', '20 us', '40 us'))
        layout.addRow(self.tr('Pulse duration:'), self.combo_pulse_duration)
        self.combo_pulse_duration.currentIndexChanged.connect(self.on_pulse_duration_changed)

        self.combo_pulse_rate: QComboBox = QComboBox(self)
        self.combo_pulse_rate.addItems(('2 Hz', '10 Hz', '40 Hz', '100 Hz'))
        layout.addRow(self.tr('Pulse rate:'), self.combo_pulse_rate)
        self.combo_pulse_rate.currentIndexChanged.connect(self.on_pulse_rate_changed)

    def __len__(self) -> int:
        return len(self.buttons)

    def __getitem__(self, index: int) -> bool:
        if 1 <= index <= len(self):
            return self.buttons[index - 1]
        else:
            return False
            # raise IndexError

    def __setitem__(self, index: int, pushed: bool) -> None:
        index -= 1
        if 0 <= index < len(self):
            self.buttons[index] = pushed

            if index == 0:
                self.setChecked(pushed)
            elif index == 1:
                self.more_emitter_voltage.setChecked(pushed)
            elif index in (2, 3):
                self.combo_amplification.setCurrentIndex(self.buttons[2] + self.buttons[3] * 2)
            elif index in (4, 5):
                self.combo_pulse_duration.setCurrentIndex(self.buttons[4] + self.buttons[5] * 2)
            elif index in (6, 7):
                self.combo_pulse_rate.setCurrentIndex(self.buttons[6] + self.buttons[7] * 2)
        # else:
        #     raise IndexError

    def __iter__(self) -> Iterator[bool]:
        yield from self.buttons

    def on_toggled(self, on: bool) -> None:
        self.buttons[0] = on

    def on_more_emitter_voltage_toggled(self, on: bool) -> None:
        self.buttons[1] = on

    def on_amplification_changed(self, index: int) -> None:
        self.buttons[2] = bool(index & 1)
        self.buttons[3] = bool(index & 2)

    def on_pulse_duration_changed(self, index: int) -> None:
        self.buttons[4] = bool(index & 1)
        self.buttons[5] = bool(index & 2)

    def on_pulse_rate_changed(self, index: int) -> None:
        self.buttons[6] = bool(index & 1)
        self.buttons[7] = bool(index & 2)
