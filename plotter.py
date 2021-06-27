# coding: utf-8
import sys
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Type

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QSettings, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QValidator, QColor
from PySide6.QtWidgets import QApplication, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, \
    QMainWindow, \
    QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget, QSizePolicy

from channel_settings import ChannelSettings
from e502 import E502, X502_ADC_FREQ_DIV_MAX

try:
    from typing import Final
except ImportError:
    # stub
    class _Final:
        @staticmethod
        def __getitem__(item: Type) -> Type:
            return item


    Final = _Final()


class Measurement(Process):
    def __init__(self, requests_queue: Queue, results_queue: Queue,
                 ip_address: str, settings: List[ChannelSettings], adc_frequency_divider: int,
                 data_portion_size: int) -> None:
        super(Measurement, self).__init__()
        self.requests_queue: Queue = requests_queue
        self.results_queue: Queue = results_queue

        self.device: E502 = E502(ip_address)
        self.device.write_channels_settings_table(settings)
        self.device.set_adc_frequency_divider(adc_frequency_divider)

        self.data_portion_size: int = data_portion_size

    def terminate(self) -> None:
        self.device.set_sync_io(False)
        self.device.stop_data_stream()

        super(Measurement, self).terminate()

    def run(self) -> None:
        self.device.enable_in_stream(from_adc=True)
        self.device.start_data_stream()
        self.device.preload_adc()
        self.device.set_sync_io(True)

        while True:
            self.results_queue.put(self.device.get_data(self.data_portion_size))


class IPAddressValidator(QValidator):
    def validate(self, text: str, text_length: int) -> QValidator.State:
        if not text:
            return QValidator.State.Invalid
        import ipaddress
        try:
            ipaddress.ip_address(text)
        except ValueError:
            if set(text).issubset(set('0123456789A''BC''DEF''a''bc''def''.:')) and not ('.' in text and ':' in text):
                return QValidator.State.Intermediate
            return QValidator.State.Invalid
        else:
            return QValidator.State.Acceptable


class FilePathEntry(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.path: Optional[Path] = None

        self.setLayout(QHBoxLayout())

        self.text: QLineEdit = QLineEdit(self)
        # TODO: on the text change,
        #  • validate the entered path and
        #  • indicate somehow if it is invalid
        self.layout().addWidget(self.text)

        self.browse_button: QPushButton = QPushButton('Browse…', self)
        # TODO: on the button click,
        #  • open a file dialog,
        #  • store the result in `path` variable,
        #  • display the result in the text box,
        #  • set the text box tooltip to the box content in case the box is too small for the path
        self.layout().addWidget(self.browse_button)

        self.layout().setStretch(1, 0)


class ChannelSettingsGUI(QGroupBox, ChannelSettings):
    channelChanged: Signal = Signal(int, name='channelChanged')
    colorChanged: Signal = Signal(QColor, name='colorChanged')

    _count: int = 0

    def __init__(self, settings: QSettings) -> None:
        QGroupBox.__init__(self, 'Enabled')
        ChannelSettings.__init__(self)

        self.settings: QSettings = settings
        settings_length: Final[int] = self.settings.beginReadArray('channelSettings')

        self._index: Final[int] = ChannelSettingsGUI._count
        self.settings.setArrayIndex(self._index)

        self.setCheckable(True)
        try:
            self.setChecked(self._count < settings_length and self.settings.value('enabled', False, bool))
        except SystemError:
            self.setChecked(False)
        self.toggled.connect(self.on_toggled)

        self.combo_range: pg.ComboBox = pg.ComboBox(self, items={'±10 V': 0, '±5 V': 1, '±2 V': 2,
                                                                 '±1 V': 3, '±0.5 V': 4, '±0.2 V': 5})
        try:
            if self._count < settings_length:
                self.combo_range.setValue(self.settings.value('range', 0, int))
        except SystemError:
            pass
        self.combo_range.currentIndexChanged.connect(self.on_combo_range_changed)
        self.range = self.combo_range.value()

        self.combo_mode: pg.ComboBox = pg.ComboBox(self, items={'Differential': 0,
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
                self.spin_channel.setValue(self.settings.value('channel', 0, int) + 1)
        except SystemError:
            pass
        self.spin_channel.valueChanged.connect(self.on_spin_channel_changed)
        self.physical_channel = self.spin_channel.value() - 1

        self.spin_averaging: QSpinBox = QSpinBox(self)
        self.spin_averaging.setRange(1, 128)
        try:
            if self._count < settings_length:
                self.spin_averaging.setValue(self.settings.value('averaging', 1, int))
        except SystemError:
            pass
        self.spin_averaging.valueChanged.connect(self.on_spin_averaging_changed)
        self.averaging = self.spin_averaging.value()

        self.color_button: pg.ColorButton = pg.ColorButton(self)
        try:
            if self._count < settings_length:
                self.spin_averaging.setValue(self.settings.value('lineColor', Qt.GlobalColor.lightGray, QColor))
        except SystemError:
            pass
        self.color_button.sigColorChanged.connect(self.on_color_changed)

        self.setLayout(QFormLayout())
        layout: QFormLayout = self.layout()
        layout.addRow('Range:', self.combo_range)
        layout.addRow('Channel:', self.spin_channel)
        layout.addRow('Mode:', self.combo_mode)
        layout.addRow('Averaging:', self.spin_averaging)
        layout.addRow('Line Color:', self.color_button)
        layout.addRow('Data File:', FilePathEntry(self))
        r: int
        for r in range(layout.rowCount()):
            layout.itemAt(r, QFormLayout.LabelRole).widget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.itemAt(r, QFormLayout.LabelRole).widget().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.settings.endArray()

        ChannelSettingsGUI._count += 1

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

    def on_color_changed(self, sender: pg.ColorButton) -> None:
        self.settings.beginWriteArray('channelSettings', self._count)
        self.settings.setArrayIndex(self._index)
        self.settings.setValue('lineColor', sender.color())
        self.settings.endArray()
        self.colorChanged.emit(sender.color())


class GUI(QMainWindow):
    def __init__(self, flags=Qt.WindowFlags()) -> None:
        super(GUI, self).__init__(flags=flags)

        self.settings: QSettings = QSettings('SavSoft', 'E-502', self)

        self.central_widget: QWidget = QWidget(self)
        self.main_layout: QHBoxLayout = QHBoxLayout(self.central_widget)
        self.controls_layout: QVBoxLayout = QVBoxLayout()
        self.parameters_box: QWidget = QWidget(self.central_widget)
        self.parameters_layout: QFormLayout = QFormLayout(self.parameters_box)
        self.buttons_layout: QHBoxLayout = QHBoxLayout()

        self.plot: pg.PlotWidget = pg.PlotWidget(self.central_widget)
        self.canvas: pg.PlotItem = self.plot.getPlotItem()
        self.plot_lines: List[pg.PlotDataItem] = []

        self.text_ip_address: QLineEdit = QLineEdit(self.parameters_box)
        self.spin_sample_rate: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_duration: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_portion_size: QSpinBox = QSpinBox(self.parameters_box)
        self.spin_frequency_divider: QSpinBox = QSpinBox(self.parameters_box)

        self.tabs: QTabWidget = QTabWidget(self.central_widget)
        self.tab: List[ChannelSettingsGUI] = [ChannelSettingsGUI(self.settings) for _ in range(8)]
        t: ChannelSettingsGUI
        for i, t in enumerate(self.tab):
            t.color_button.setColor(pg.intColor(i, hues=len(self.tab)))

        self.button_start: QPushButton = QPushButton(self.central_widget)
        self.button_stop: QPushButton = QPushButton(self.central_widget)

        self.setup_ui_appearance()
        self.load_settings()
        self.setup_actions()

    def setup_ui_appearance(self) -> None:
        opts: Dict[str, Union[bool, str, int]]
        opts = {
            'suffix': 'S/s',
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
            'suffix': 's',
            'siPrefix': False,
            'decimals': 1,
            'dec': True,
            'compactHeight': False,
            'minStep': 0.1,
            'format': '{value:.{decimals}f}{suffixGap}{suffix}',
            'bounds': (1.0, np.inf)
        }
        self.spin_duration.setOpts(**opts)

        self.spin_portion_size.setRange(1, 65535)
        self.spin_frequency_divider.setRange(1, X502_ADC_FREQ_DIV_MAX)

        self.text_ip_address.setValidator(IPAddressValidator())

        self.plot.setFocusPolicy(Qt.ClickFocus)

        self.main_layout.addWidget(self.plot)
        self.main_layout.addLayout(self.controls_layout)
        self.controls_layout.addWidget(self.parameters_box)
        self.controls_layout.addWidget(self.tabs)
        self.controls_layout.addLayout(self.buttons_layout)

        self.parameters_layout.addRow('IP Address:', self.text_ip_address)
        self.parameters_layout.addRow('Sample Rate:', self.spin_sample_rate)
        self.parameters_layout.addRow('Measurement Duration:', self.spin_duration)
        self.parameters_layout.addRow('Portion Size:', self.spin_portion_size)
        self.parameters_layout.addRow('Sync Input Frequency Divider:', self.spin_frequency_divider)

        index: int
        for index in range(8):
            self.tabs.addTab(self.tab[index], str(index + 1))

        self.buttons_layout.addWidget(self.button_start)
        self.buttons_layout.addWidget(self.button_stop)

        self.button_start.setText('Start')
        self.button_stop.setText('Stop')
        self.button_stop.setDisabled(True)

        self.setCentralWidget(self.central_widget)

        any_channel_active: bool = any(t.isChecked() for t in self.tab)
        self.button_start.setEnabled(any_channel_active)

    def setup_actions(self) -> None:
        self.button_start.clicked.connect(self.on_button_start_clicked)
        self.button_stop.clicked.connect(self.on_button_stop_clicked)

        index: int
        for index in range(8):
            self.tab[index].channelChanged.connect(self.on_tab_channel_changed)
            self.tab[index].toggled.connect(self.on_tab_toggled)
            self.tab[index].colorChanged.connect(self.on_tab_color_changed)

    def load_settings(self) -> None:
        self.restoreGeometry(self.settings.value('windowGeometry', b''))
        self.restoreState(self.settings.value('windowState', b''))

        self.settings.beginGroup('parameters')
        self.text_ip_address.setText(self.settings.value('ipAddress', '192.168.0.1', str))
        self.spin_sample_rate.setValue(self.settings.value('sampleRate', 2e6, float))
        self.spin_duration.setValue(self.settings.value('measurementDuration', 60.0, float))
        self.spin_portion_size.setValue(self.settings.value('samplesPortionSize', 1000, int))
        self.spin_frequency_divider.setValue(self.settings.value('frequencyDivider', 1, int))
        self.settings.endGroup()

    def save_settings(self) -> None:
        self.settings.setValue('windowGeometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

        self.settings.beginGroup('parameters')
        self.settings.setValue('ipAddress', self.text_ip_address.text())
        self.settings.setValue('sampleRate', self.spin_sample_rate.value())
        self.settings.setValue('measurementDuration', self.spin_duration.value())
        self.settings.setValue('samplesPortionSize', self.spin_portion_size.value())
        self.settings.setValue('frequencyDivider', self.spin_frequency_divider.value())
        self.settings.endGroup()

        self.settings.sync()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def on_button_start_clicked(self) -> None:
        self.button_start.setDisabled(True)
        self.parameters_box.setDisabled(True)
        self.tabs.setDisabled(True)
        self.button_stop.setEnabled(True)

    def on_button_stop_clicked(self) -> None:
        self.button_stop.setDisabled(True)
        self.parameters_box.setEnabled(True)
        self.tabs.setEnabled(True)
        self.button_start.setEnabled(True)

    def on_tab_channel_changed(self, channel: int) -> None:
        index: int
        tab: ChannelSettingsGUI
        tab_index: int = self.tabs.indexOf(self.sender())
        for index, tab in enumerate(self.tab):
            if index == tab_index:
                continue
            if channel == tab.physical_channel:
                tab.setChecked(False)

    def on_tab_toggled(self, on: bool) -> None:
        any_channel_active: bool = any(t.isChecked() for t in self.tab)
        self.button_start.setEnabled(any_channel_active)
        self.button_stop.setDisabled(any_channel_active)
        if not on:
            return
        other_channels: Set[int] = set()
        tab: ChannelSettingsGUI
        for tab in self.tab:
            if tab.isChecked() and tab is not self.sender():
                other_channels.add(tab.physical_channel)
        self.sender().spin_channel.setValue(min(set(list(range(self.sender().spin_channel.minimum() - 1,
                                                               self.sender().spin_channel.maximum())))
                                                .difference(other_channels)) + 1)

    def on_tab_color_changed(self, color: QColor) -> None:
        for line, tab in zip(self.plot_lines, self.tab):
            if self.sender() is tab:
                line.setPen(color)


class App(GUI):
    def __init__(self, flags=Qt.WindowFlags()) -> None:
        super(App, self).__init__(flags=flags)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

        self.requests_queue: Queue = Queue()
        self.results_queue: Queue = Queue()
        self.measurement: Optional[Measurement] = None

    def on_button_start_clicked(self) -> None:
        super(App, self).on_button_start_clicked()
        active_settings: List[ChannelSettingsGUI] = [t for t in self.tab if t.isChecked()]
        self.canvas.clearPlots()
        self.plot_lines = [self.canvas.plot([], [],
                                            name=f'{t.physical_channel}',
                                            pen=t.color_button.color())
                           for t in active_settings]
        self.timer.start(10)
        self.measurement = Measurement(self.requests_queue, self.results_queue,
                                       ip_address=self.text_ip_address.text(),
                                       settings=active_settings,
                                       adc_frequency_divider=self.spin_frequency_divider.value(),
                                       data_portion_size=self.spin_portion_size.value())
        self.measurement.start()

    def on_button_stop_clicked(self) -> None:
        if self.measurement is not None:
            self.measurement.terminate()
            self.measurement.join()
        self.timer.stop()
        super(App, self).on_button_stop_clicked()

    def on_timeout(self) -> None:
        while not self.results_queue.empty():
            data: np.ndarray = self.results_queue.get()
            ch: int
            for ch, line in zip(range(data.shape[1]), self.plot_lines):
                line.setData(data[..., ch])
                # TODO:
                #  • display not only one data junk but the whole trend, up to the specified length,
                #  • store the received data into the specified files (if a path is given)


if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)
    window: App = App()
    window.show()
    app.exec()
