# coding: utf-8

from __future__ import annotations

from typing import cast

from pyqtgraph import ComboBox, ColorButton

from channel_settings import ChannelSettings as _ChannelSettings
from gui.file_path_entry import FilePathEntry
from gui.pg_qt import *
from stubs import Final

__all__ = ['ChannelSettings']


class ChannelSettings(QGroupBox, _ChannelSettings):
    channelChanged: Signal = Signal(int, name='channelChanged')
    colorChanged: Signal = Signal(QColor, name='colorChanged')

    _count: int = 0

    def __init__(self, settings: QSettings) -> None:
        QGroupBox.__init__(self, 'Enabled')
        _ChannelSettings.__init__(self)

        self.settings: QSettings = settings
        settings_length: Final[int] = self.settings.beginReadArray('channelSettings')

        self._index: Final[int] = ChannelSettings._count
        self.settings.setArrayIndex(self._index)

        self.setCheckable(True)
        try:
            self.setChecked(self._count < settings_length and cast(bool, self.settings.value('enabled', False, bool)))
        except SystemError:
            self.setChecked(False)
        self.toggled.connect(self.on_toggled)

        self.combo_range: ComboBox = ComboBox(self, items={'±10 V': 0, '±5 V': 1, '±2 V': 2,
                                                           '±1 V': 3, '±0.5 V': 4, '±0.2 V': 5})
        try:
            if self._count < settings_length:
                self.combo_range.setValue(self.settings.value('range', 0, int))
        except SystemError:
            pass
        self.combo_range.currentIndexChanged.connect(self.on_combo_range_changed)
        self.range = self.combo_range.value()

        self.combo_mode: ComboBox = ComboBox(self, items={'Differential': 0,
                                                          'Channels 1 to 16 with common GND': 1,
                                                          'Channels 16 to 32 with common GND': 2,
                                                          'Grounded ADC': 3})
        try:
            if self._count < settings_length:
                self.combo_mode.setValue(self.settings.value('mode', 0, int))
        except SystemError:
            pass
        self.combo_mode.currentIndexChanged.connect(self.on_combo_mode_changed)
        self.mode = self.combo_mode.value()

        self.spin_channel: QSpinBox = QSpinBox(self)
        if self.mode == 2:
            self.spin_channel.setRange(17, 32)
        else:
            self.spin_channel.setRange(1, 16)
        try:
            if self._count < settings_length:
                self.spin_channel.setValue(cast(int, self.settings.value('channel', 0, int)) + 1)
        except SystemError:
            pass
        self.spin_channel.valueChanged.connect(self.on_spin_channel_changed)
        self.physical_channel = self.spin_channel.value() - 1

        self.spin_averaging: QSpinBox = QSpinBox(self)
        self.spin_averaging.setRange(1, 128)
        try:
            if self._count < settings_length:
                self.spin_averaging.setValue(cast(int, self.settings.value('averaging', 1, int)))
        except SystemError:
            pass
        self.spin_averaging.valueChanged.connect(self.on_spin_averaging_changed)
        self.averaging = self.spin_averaging.value()

        self.color_button: ColorButton = ColorButton(self)
        try:
            if self._count < settings_length:
                self.color_button.setColor(self.settings.value('lineColor', QColor(Qt.GlobalColor.lightGray), QColor))
        except SystemError:
            pass
        self.color_button.sigColorChanged.connect(self.on_color_changed)

        self.saving_location: FilePathEntry = FilePathEntry(cast(str, self.settings.value('savingLocation', '', str)),
                                                            self)

        self.setLayout(QFormLayout())
        layout: QFormLayout = cast(QFormLayout, self.layout())
        layout.addRow('Range:', self.combo_range)
        layout.addRow('Channel:', self.spin_channel)
        layout.addRow('Mode:', self.combo_mode)
        layout.addRow('Averaging:', self.spin_averaging)
        layout.addRow('Line Color:', self.color_button)
        layout.addRow('Data File:', self.saving_location)
        r: int
        for r in range(layout.rowCount()):
            layout.itemAt(r, QFormLayout.ItemRole.LabelRole).widget().setSizePolicy(QSizePolicy.Policy.Expanding,
                                                                                    QSizePolicy.Policy.Expanding)
            layout.itemAt(r, QFormLayout.ItemRole.LabelRole).widget().setAlignment(Qt.AlignmentFlag.AlignLeft
                                                                                   | Qt.AlignmentFlag.AlignVCenter)

        self.settings.endArray()

        ChannelSettings._count += 1

    def on_toggled(self, on: bool) -> None:
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('enabled', on)
        self.settings.endArray()

    def on_combo_range_changed(self, _index: int) -> None:
        self.range = self.combo_range.value()
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('range', self.range)
        self.settings.endArray()

    def on_spin_channel_changed(self, new_value: int) -> None:
        self.physical_channel = new_value - 1
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('channel', self.physical_channel)
        self.settings.endArray()
        self.channelChanged.emit(self.physical_channel)

    def on_combo_mode_changed(self, _index: int) -> None:
        self.mode = self.combo_mode.value()
        if self.mode == 2:
            self.spin_channel.setRange(17, 32)
        elif self.mode != 3:
            self.spin_channel.setRange(0, 16)
        self.spin_channel.setDisabled(self.mode == 3)
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('mode', self.mode)
        self.settings.endArray()
        self.channelChanged.emit(self.physical_channel)

    def on_spin_averaging_changed(self, new_value: int) -> None:
        self.averaging = new_value
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('averaging', self.averaging)
        self.settings.endArray()

    def on_color_changed(self, sender: ColorButton) -> None:
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('lineColor', sender.color())
        self.settings.endArray()
        self.colorChanged.emit(sender.color())
