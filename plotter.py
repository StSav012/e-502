# coding: utf-8
import sys
import time
from multiprocessing import Process, Queue
from typing import Dict, List, Union

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QSettings, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QValidator
from PySide6.QtWidgets import QApplication, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, \
    QMainWindow, \
    QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget

from channel_settings import ChannelSettings


class Measurement(Process):
    def __init__(self, requests_queue: Queue, results_queue: Queue) -> None:
        super(Measurement, self).__init__()
        self.requests_queue: Queue = requests_queue
        self.results_queue: Queue = results_queue

    def terminate(self):
        super(Measurement, self).terminate()

    def run(self):
        while True:
            self.results_queue.put(np.column_stack((np.linspace(0, 0.5, 100), np.random.normal(size=100))))
            time.sleep(0.5)


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


class ChannelSettingsGUI(QGroupBox, ChannelSettings):
    channelChanged: Signal = Signal(int, name='channelChanged')

    def __init__(self):
        super().__init__()

        self.setCheckable(True)
        self.setChecked(False)

        self.combo_range: pg.ComboBox = pg.ComboBox(self, items={'±10 V': 0,
                                                                 '±5 V': 1, '±2 V': 2, '±1 V': 3,
                                                                 '±0.5 V': 4, '±0.2 V': 5})
        self.combo_range.currentIndexChanged.connect(self.on_combo_range_changed)

        self.spin_channel: QSpinBox = QSpinBox(self)
        self.spin_channel.setRange(1, 16)
        self.spin_channel.valueChanged.connect(self.on_spin_channel_changed)

        self.combo_mode: pg.ComboBox = pg.ComboBox(self, items={'Differential': 0,
                                                                'Channels 1 to 16 with common GND': 1,
                                                                'Channels 16 to 32 with common GND': 2,
                                                                'Grounded ADC': 3})
        self.combo_mode.currentIndexChanged.connect(self.on_combo_mode_changed)

        self.spin_averaging: QSpinBox = QSpinBox(self)

        self.setLayout(QFormLayout())
        self.layout().addRow('Range', self.combo_range)
        self.layout().addRow('Channel', self.spin_channel)
        self.layout().addRow('Mode', self.combo_mode)
        self.layout().addRow('Averaging', self.spin_averaging)

    def on_combo_range_changed(self, _index: int) -> None:
        self.range = self.combo_range.value()

    def on_spin_channel_changed(self, new_value: int) -> None:
        self.physical_channel = new_value - 1
        self.channelChanged.emit(self.physical_channel)

    def on_combo_mode_changed(self, _index: int) -> None:
        self.mode = self.combo_mode.value()
        if self.mode == 2:
            self.spin_channel.setRange(17, 32)
        elif self.mode != 3:
            self.spin_channel.setRange(0, 16)
        self.spin_channel.setDisabled(self.mode == 3)

    # TODO:
    #  − add sync between the channel properties and the GUI
    #  − limit the channel and the averaging according to the mode and the sample rate required
    #  − avoid selecting same physical channel more than once


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

        self.figure: pg.PlotWidget = pg.PlotWidget(self.central_widget)
        self.plot_line: pg.PlotDataItem = self.figure.plot(np.empty(0), name='')

        self.text_ip_address: QLineEdit = QLineEdit(self.parameters_box)
        self.spin_sample_rate: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_duration: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_portion_size: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_frequency_divider: pg.SpinBox = pg.SpinBox(self.parameters_box)

        self.tabs: QTabWidget = QTabWidget(self.central_widget)
        self.tab: List[ChannelSettingsGUI] = [ChannelSettingsGUI() for _ in range(8)]

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
        opts = {
            'suffix': '',
            'siPrefix': False,
            'decimals': 0,
            'dec': True,
            'compactHeight': False,
            'minStep': 1,
            'format': '{value:.{decimals}f}{suffixGap}{suffix}',
            'bounds': (1, np.inf)
        }
        self.spin_portion_size.setOpts(**opts)
        self.spin_frequency_divider.setOpts(**opts)

        self.text_ip_address.setValidator(IPAddressValidator())

        self.figure.setFocusPolicy(Qt.ClickFocus)

        self.main_layout.addWidget(self.figure)
        self.main_layout.addLayout(self.controls_layout)
        self.controls_layout.addWidget(self.parameters_box)
        self.controls_layout.addWidget(self.tabs)
        self.controls_layout.addLayout(self.buttons_layout)

        self.parameters_layout.addRow('IP Address', self.text_ip_address)
        self.parameters_layout.addRow('Sample Rate', self.spin_sample_rate)
        self.parameters_layout.addRow('Measurement Duration', self.spin_duration)
        self.parameters_layout.addRow('Portion Size', self.spin_portion_size)
        self.parameters_layout.addRow('Sync Input Frequency Divider', self.spin_frequency_divider)

        index: int
        for index in range(8):
            self.tabs.addTab(self.tab[index], str(index + 1))

        self.buttons_layout.addWidget(self.button_start)
        self.buttons_layout.addWidget(self.button_stop)

        self.button_start.setText('Start')
        self.button_stop.setText('Stop')
        self.button_stop.setDisabled(True)

        self.setCentralWidget(self.central_widget)

    def setup_actions(self):
        self.button_start.clicked.connect(self.on_button_start_clicked)
        self.button_stop.clicked.connect(self.on_button_stop_clicked)

        index: int
        for index in range(8):
            self.tab[index].channelChanged.connect(lambda channel: self.on_tab_channel_changed(index, channel))

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

    def on_tab_channel_changed(self, tab_index: int, channel: int) -> None:
        index: int
        tab: ChannelSettingsGUI
        for index, tab in enumerate(self.tab):
            if index == tab_index:
                continue
            if channel == tab.physical_channel:
                tab.setChecked(False)


class App(GUI):
    def __init__(self, flags=Qt.WindowFlags()) -> None:
        super(App, self).__init__(flags=flags)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

        self.requests_queue: Queue = Queue()
        self.results_queue: Queue = Queue()
        self.measurement: Measurement = Measurement(self.requests_queue, self.results_queue)

    def on_button_start_clicked(self) -> None:
        super(App, self).on_button_start_clicked()
        self.timer.start(10)
        self.measurement = Measurement(self.requests_queue, self.results_queue)
        self.measurement.start()

    def on_button_stop_clicked(self) -> None:
        self.measurement.terminate()
        self.measurement.join()
        self.timer.stop()
        super(App, self).on_button_stop_clicked()

    def on_timeout(self):
        if not self.results_queue.empty():
            self.plot_line.setData(self.results_queue.get())


if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)
    window: App = App()
    window.show()
    app.exec()
