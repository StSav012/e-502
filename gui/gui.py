# coding: utf-8

from __future__ import annotations

from pathlib import Path
from typing import cast, Dict, List, Sequence, Set, Tuple, Union

import numpy as np
import pyqtgraph as pg  # type: ignore

from e502 import X502_ADC_FREQ_DIV_MAX
from gui.channel_settings import ChannelSettings
from gui.digital_lines import DigitalLines
from gui.dir_path_entry import DirPathEntry
from gui.ip_address_entry import IPAddressEntry
from gui.pg_qt import *
from stubs import Final

__all__ = ['GUI']


class GUI(QMainWindow):
    CHANNEL_NAMES: Final[Sequence[str]] = (
        'Sync',
        'Signal'
    )

    def __init__(self) -> None:
        super(GUI, self).__init__()

        self.settings: QSettings = QSettings('config.ini', QSettings.Format.IniFormat, self)

        self.central_widget: QWidget = QWidget(self)
        self.main_layout: QHBoxLayout = QHBoxLayout(self.central_widget)
        self.scrollable_box: QScrollArea = QScrollArea(self.central_widget)
        self.controls_box: QWidget = QWidget(self.central_widget)
        self.controls_layout: QVBoxLayout = QVBoxLayout(self.controls_box)
        self.parameters_box: QWidget = QWidget(self.central_widget)
        self.parameters_layout: QFormLayout = QFormLayout(self.parameters_box)
        self.buttons_layout: QHBoxLayout = QHBoxLayout()

        self.text_ip_address: IPAddressEntry = IPAddressEntry(self.parameters_box)
        self.spin_sample_rate: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_duration: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_portion_size: QSpinBox = QSpinBox(self.parameters_box)
        self.spin_frequency_divider: QSpinBox = QSpinBox(self.parameters_box)
        self.digital_lines: DigitalLines = DigitalLines(parent=self.parameters_box)

        self.saving_location: DirPathEntry = DirPathEntry('', self)

        self.tabs_container: QTabWidget = QTabWidget(self.central_widget)
        self.tabs: List[ChannelSettings] = [ChannelSettings(self.settings) for _ in range(len(GUI.CHANNEL_NAMES))]

        self.button_start: QPushButton = QPushButton(self.central_widget)
        self.button_stop: QPushButton = QPushButton(self.central_widget)

        self.setup_ui_appearance()
        self.load_settings()
        self.setup_actions()

    def setup_ui_appearance(self) -> None:
        opts: Dict[str, Union[bool, str, int, float, Tuple[float, float]]]
        opts = {
            'suffix': self.tr('S/s', 'unit: samples per second'),
            'siPrefix': True,
            'decimals': 3,
            'dec': True,
            'compactHeight': False,
            'minStep': 0.001,
            'format': '{scaledValue:.{decimals}f}{suffixGap}{siPrefix}{suffix}',
            'bounds': (0.0, 2e6),
        }
        self.spin_sample_rate.setOpts(**opts)
        opts = {
            'suffix': self.tr('s', 'unit: seconds'),
            'siPrefix': False,
            'decimals': 1,
            'dec': True,
            'compactHeight': False,
            'minStep': 0.1,
            'format': '{value:.{decimals}f}{suffixGap}{suffix}',
            'bounds': (1.0, np.inf)
        }
        self.spin_duration.setOpts(**opts)

        self.spin_portion_size.setRange(1, 1_000_000)
        self.spin_frequency_divider.setRange(1, X502_ADC_FREQ_DIV_MAX)

        self.main_layout.addWidget(self.scrollable_box)
        self.controls_layout.addWidget(self.parameters_box)
        self.controls_layout.addWidget(self.digital_lines)
        self.controls_layout.addStretch(1)
        self.controls_layout.addWidget(self.tabs_container)
        self.controls_layout.addLayout(self.buttons_layout)

        # https://forum.qt.io/post/129727
        self.scrollable_box.setWidgetResizable(True)
        self.scrollable_box.setFrameStyle(QFrame.Shape.NoFrame)
        self.scrollable_box.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollable_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollable_box.setWidget(self.controls_box)
        self.controls_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.scrollable_box.setMinimumWidth(self.controls_box.minimumSizeHint().width()
                                            + self.scrollable_box.verticalScrollBar().width())

        self.digital_lines.setTitle(self.tr('Digital Lines'))

        self.parameters_layout.addRow(self.tr('IP address:'), self.text_ip_address)
        self.parameters_layout.addRow(self.tr('Sample rate:'), self.spin_sample_rate)
        self.parameters_layout.addRow(self.tr('Measurement duration:'), self.spin_duration)
        self.parameters_layout.addRow(self.tr('Portion size:'), self.spin_portion_size)
        self.parameters_layout.addRow(self.tr('Sync input frequency divider:'), self.spin_frequency_divider)
        self.parameters_layout.addRow(self.tr('Data location:'), self.saving_location)

        title: str
        t: ChannelSettings
        for title, t in zip(GUI.CHANNEL_NAMES, self.tabs):
            self.tabs_container.addTab(t, self.tr(title))

        self.buttons_layout.addWidget(self.button_start)
        self.buttons_layout.addWidget(self.button_stop)

        self.button_start.setText(self.tr('Start'))
        self.button_stop.setText(self.tr('Stop'))
        self.button_stop.setDisabled(True)

        self.setCentralWidget(self.central_widget)

        any_channel_active: bool = any(t.isChecked() for t in self.tabs)
        self.button_start.setEnabled(any_channel_active)

    def setup_actions(self) -> None:
        self.button_start.clicked.connect(self.on_button_start_clicked)
        self.button_stop.clicked.connect(self.on_button_stop_clicked)

        index: int
        for index in range(len(self.tabs)):
            self.tabs[index].channelChanged.connect(self.on_tab_channel_changed)
            self.tabs[index].toggled.connect(self.on_tab_toggled)

    def load_settings(self) -> None:
        window_frame: QRect = self.frameGeometry()
        desktop_center: QPoint = self.screen().availableGeometry().center()
        window_frame.moveCenter(desktop_center)
        self.move(window_frame.topLeft())
        self.restoreGeometry(cast(QByteArray, self.settings.value('windowGeometry', QByteArray())))
        self.restoreState(cast(QByteArray, self.settings.value('windowState', QByteArray())))

        self.settings.beginGroup('parameters')
        self.text_ip_address.text = cast(str, self.settings.value('ipAddress', '192.168.0.1', str))
        self.spin_sample_rate.setValue(cast(float, self.settings.value('sampleRate', 2e6, float)))
        self.spin_duration.setValue(cast(float, self.settings.value('measurementDuration', 60.0, float)))
        self.spin_portion_size.setValue(cast(int, self.settings.value('samplesPortionSize', 1000, int)))
        self.spin_frequency_divider.setValue(cast(int, self.settings.value('frequencyDivider', 1, int)))
        self.saving_location.text.setText(cast(str, self.settings.value('savingLocation', str(Path.cwd()), str)))
        self.settings.endGroup()

        i: int
        for i in range(self.settings.beginReadArray('digitalLines')):
            self.settings.setArrayIndex(i)
            self.digital_lines[i + 1] = cast(bool, self.settings.value('pushed', False, bool))
        self.settings.endArray()

    def save_settings(self) -> None:
        self.settings.setValue('windowGeometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

        self.settings.beginGroup('parameters')
        self.settings.setValue('ipAddress', self.text_ip_address.text)
        self.settings.setValue('sampleRate', self.spin_sample_rate.value())
        self.settings.setValue('measurementDuration', self.spin_duration.value())
        self.settings.setValue('samplesPortionSize', self.spin_portion_size.value())
        self.settings.setValue('frequencyDivider', self.spin_frequency_divider.value())
        self.settings.setValue('savingLocation', str(self.saving_location.path))
        self.settings.endGroup()

        self.settings.beginWriteArray('digitalLines', len(self.digital_lines))
        i: int
        on: bool
        for i, on in enumerate(self.digital_lines):
            self.settings.setArrayIndex(i)
            self.settings.setValue('pushed', on)
        self.settings.endArray()

        self.settings.sync()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def on_button_start_clicked(self) -> None:
        self.button_start.setDisabled(True)
        self.parameters_box.setDisabled(True)
        self.digital_lines.setDisabled(True)
        self.tabs_container.setDisabled(True)
        self.button_stop.setEnabled(True)

    def on_button_stop_clicked(self) -> None:
        self.button_stop.setDisabled(True)
        self.parameters_box.setEnabled(True)
        self.digital_lines.setEnabled(True)
        self.tabs_container.setEnabled(True)
        self.button_start.setEnabled(True)

    def on_tab_channel_changed(self, channel: int) -> None:
        index: int
        tab: ChannelSettings
        tab_index: int = self.tabs_container.indexOf(self.sender())
        for index, tab in enumerate(self.tabs):
            if index == tab_index:
                continue
            if channel == tab.physical_channel:
                tab.setChecked(False)

    def on_tab_toggled(self, on: bool) -> None:
        any_channel_active: bool = any(t.isChecked() for t in self.tabs)
        self.button_start.setEnabled(any_channel_active)

        if not on:
            return

        other_channels: Set[int] = set()
        for tab in self.tabs:
            if tab.isChecked() and tab is not self.sender() and tab.physical_channel is not None:
                other_channels.add(tab.physical_channel)
        self.sender().spin_channel.setValue(min(set(list(range(self.sender().spin_channel.minimum() - 1,
                                                               self.sender().spin_channel.maximum())))
                                                .difference(other_channels)) + 1)
