# coding: utf-8

from __future__ import annotations

import sys
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, TextIO, Tuple, Union, cast, Iterator, Sequence

import numpy as np
import pathvalidate
import pyqtgraph as pg  # type: ignore
if pg.Qt.QT_LIB == pg.Qt.PYSIDE6:
    from PySide6.QtCore import QSettings, QTimer, Qt, Signal, QByteArray, QRect, QPoint
    from PySide6.QtGui import QCloseEvent, QColor, QValidator, QPalette, QPaintEvent
    from PySide6.QtWidgets import QApplication, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, \
        QMainWindow, QPushButton, QSizePolicy, QSpinBox, QStyle, QTabWidget, QVBoxLayout, QWidget
elif pg.Qt.QT_LIB == pg.Qt.PYQT5:
    from PyQt5.QtCore import QSettings, QTimer, Qt, pyqtSignal as Signal, QByteArray, QRect, QPoint
    from PyQt5.QtGui import QCloseEvent, QColor, QValidator, QPalette, QPaintEvent
    from PyQt5.QtWidgets import QApplication, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, \
        QMainWindow, QPushButton, QSizePolicy, QSpinBox, QStyle, QTabWidget, QVBoxLayout, QWidget
elif pg.Qt.QT_LIB == pg.Qt.PYSIDE2:
    from PySide2.QtCore import QSettings, QTimer, Qt, Signal, QByteArray, QRect, QPoint
    from PySide2.QtGui import QCloseEvent, QColor, QValidator, QPalette, QPaintEvent
    from PySide2.QtWidgets import QApplication, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, \
        QMainWindow, QPushButton, QSizePolicy, QSpinBox, QStyle, QTabWidget, QVBoxLayout, QWidget
    QApplication.exec = QApplication.exec_
else:
    raise Exception('PySide6, PyQt5, or PySide2, is required. PyQt6 is not supported.')

from channel_settings import ChannelSettings
from e502 import E502, X502_ADC_FREQ_DIV_MAX

from stubs import Final, Literal

FileWritingMode = Literal['w', 'w+', '+w', 'wt', 'tw', 'wt+', 'w+t', '+wt', 'tw+', 't+w', '+tw',
                          'a', 'a+', '+a', 'at', 'ta', 'at+', 'a+t', '+at', 'ta+', 't+a', '+ta',
                          'x', 'x+', '+x', 'xt', 'tx', 'xt+', 'x+t', '+xt', 'tx+', 't+x', '+tx']


class Measurement(Process):
    def __init__(self, results_queue: Queue[np.ndarray],
                 ip_address: str, settings: Sequence[ChannelSettings], adc_frequency_divider: int,
                 data_portion_size: int, digital_lines: DigitalLinesGUI) -> None:
        super(Measurement, self).__init__()
        self.results_queue: Queue[np.ndarray] = results_queue

        self.device: E502 = E502(ip_address)
        self.device.write_channels_settings_table(settings)
        self.device.set_adc_frequency_divider(adc_frequency_divider)

        self.data_portion_size: int = data_portion_size
        self.digital_lines: DigitalLinesGUI = digital_lines

    def terminate(self) -> None:
        self.device.set_sync_io(False)
        self.device.stop_data_stream()

        super(Measurement, self).terminate()

    def run(self) -> None:
        i: int
        on: bool
        for i, on in enumerate(self.digital_lines):
            self.device.write_digital(i, on)

        self.device.enable_in_stream(from_adc=True)
        self.device.start_data_stream()
        self.device.preload_adc()
        self.device.set_sync_io(True)

        while True:
            self.results_queue.put(self.device.get_data(self.data_portion_size))


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


class FilePathEntry(QWidget):
    def __init__(self, initial_file_path: str = '', parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.path: Optional[Path] = None

        self.setLayout(QHBoxLayout())

        self.text: QLineEdit = QLineEdit(self)
        self.text.setText(initial_file_path)
        self.text.textChanged.connect(self.on_text_changed)
        self.layout().addWidget(self.text)

        self.status: QLabel = QLabel(self)
        self.layout().addWidget(self.status)

        self.browse_button: QPushButton = QPushButton('Browse…', self)
        self.browse_button.clicked.connect(self.on_browse_button_clicked)
        self.layout().addWidget(self.browse_button)

        self.layout().setStretch(1, 0)
        self.layout().setStretch(2, 0)

    def on_text_changed(self, text: str) -> None:
        """ display an icon showing whether the entered file name is acceptable """

        self.text.setToolTip(text)

        if not text:
            self.status.clear()
            self.path = None
            return

        path: Path = Path(text).resolve()
        if path.is_dir():
            self.status.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(self.text.height()))
            self.path = None
            return
        if path.exists():
            self.status.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(self.text.height()))
            self.path = path
            return
        try:
            pathvalidate.validate_filepath(path, platform='auto')
        except pathvalidate.error.ValidationError as ex:
            print(ex.description)
            self.status.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(self.text.height()))
            self.path = None
        else:
            self.status.clear()
            self.path = path

    def on_browse_button_clicked(self) -> None:
        new_file_name: str
        new_file_name, _ = QFileDialog.getSaveFileName(
            self, 'Save As...',
            str(self.path or ''),
            'Tab Separated Values (*.tsv)')
        if new_file_name:
            self.text.setText(new_file_name)


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
            self.setChecked(self._count < settings_length and cast(bool, self.settings.value('enabled', False, bool)))
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

        self.color_button: pg.ColorButton = pg.ColorButton(self)
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


class DigitalLinesGUI(QGroupBox):
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


class GUI(QMainWindow):
    def __init__(self, flags: Qt.WindowFlags = Qt.WindowFlags()) -> None:
        super(GUI, self).__init__(flags=flags)

        self.settings: QSettings = QSettings('SavSoft', 'E-502', self)

        self.central_widget: QWidget = QWidget(self)
        self.main_layout: QHBoxLayout = QHBoxLayout(self.central_widget)
        self.controls_layout: QVBoxLayout = QVBoxLayout()
        self.parameters_box: QWidget = QWidget(self.central_widget)
        self.parameters_layout: QFormLayout = QFormLayout(self.parameters_box)
        self.buttons_layout: QHBoxLayout = QHBoxLayout()

        self.text_ip_address: QLineEdit = QLineEdit(self.parameters_box)
        self.spin_sample_rate: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_duration: pg.SpinBox = pg.SpinBox(self.parameters_box)
        self.spin_portion_size: QSpinBox = QSpinBox(self.parameters_box)
        self.spin_frequency_divider: QSpinBox = QSpinBox(self.parameters_box)
        self.digital_lines: DigitalLinesGUI = DigitalLinesGUI(parent=self.parameters_box)

        self.tabs_container: QTabWidget = QTabWidget(self.central_widget)
        self.tabs: List[ChannelSettingsGUI] = [ChannelSettingsGUI(self.settings) for _ in range(8)]
        i: int
        t: ChannelSettingsGUI
        for i, t in enumerate(self.tabs):
            t.color_button.setColor(pg.intColor(i, hues=len(self.tabs)))

        self.plot: pg.GraphicsLayoutWidget = pg.GraphicsLayoutWidget(self.central_widget)
        self.canvases: List[pg.PlotItem] = [self.plot.addPlot(row=i, col=0) for i in range(len(self.tabs))]
        self.plot_lines: List[pg.PlotDataItem] = []

        self.button_start: QPushButton = QPushButton(self.central_widget)
        self.button_stop: QPushButton = QPushButton(self.central_widget)

        self.setup_ui_appearance()
        self.load_settings()
        self.setup_actions()

    def setup_ui_appearance(self) -> None:
        opts: Dict[str, Union[bool, str, int, float, Tuple[float, float]]]
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

        self.spin_portion_size.setRange(1, 1_000_000)
        self.spin_frequency_divider.setRange(1, X502_ADC_FREQ_DIV_MAX)

        self.text_ip_address.setValidator(IPAddressValidator())

        self.plot.setFocusPolicy(Qt.ClickFocus)

        self.main_layout.addWidget(self.plot)
        self.main_layout.addLayout(self.controls_layout)
        self.controls_layout.addWidget(self.parameters_box)
        self.controls_layout.addWidget(self.digital_lines)
        self.controls_layout.addStretch(1)
        self.controls_layout.addWidget(self.tabs_container)
        self.controls_layout.addLayout(self.buttons_layout)

        self.digital_lines.setTitle('Digital Lines')

        self.parameters_layout.addRow('IP Address:', self.text_ip_address)
        self.parameters_layout.addRow('Sample Rate:', self.spin_sample_rate)
        self.parameters_layout.addRow('Measurement Duration:', self.spin_duration)
        self.parameters_layout.addRow('Portion Size:', self.spin_portion_size)
        self.parameters_layout.addRow('Sync Input Frequency Divider:', self.spin_frequency_divider)

        i: int
        t: ChannelSettingsGUI
        for i, t in enumerate(self.tabs):
            self.tabs_container.addTab(t, str(i + 1))

        self.buttons_layout.addWidget(self.button_start)
        self.buttons_layout.addWidget(self.button_stop)

        self.button_start.setText('Start')
        self.button_stop.setText('Stop')
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
            self.tabs[index].colorChanged.connect(self.on_tab_color_changed)

    def load_settings(self) -> None:
        window_frame: QRect = self.frameGeometry()
        desktop_center: QPoint = self.screen().availableGeometry().center()
        window_frame.moveCenter(desktop_center)
        self.move(window_frame.topLeft())
        self.restoreGeometry(cast(QByteArray, self.settings.value('windowGeometry', QByteArray())))
        self.restoreState(cast(QByteArray, self.settings.value('windowState', QByteArray())))

        self.settings.beginGroup('parameters')
        self.text_ip_address.setText(cast(str, self.settings.value('ipAddress', '192.168.0.1', str)))
        self.spin_sample_rate.setValue(cast(float, self.settings.value('sampleRate', 2e6, float)))
        self.spin_duration.setValue(cast(float, self.settings.value('measurementDuration', 60.0, float)))
        self.spin_portion_size.setValue(cast(int, self.settings.value('samplesPortionSize', 1000, int)))
        self.spin_frequency_divider.setValue(cast(int, self.settings.value('frequencyDivider', 1, int)))
        self.settings.endGroup()

        i: int
        for i in range(self.settings.beginReadArray('digitalLines')):
            self.settings.setArrayIndex(i)
            self.digital_lines[i + 1] = cast(bool, self.settings.value('pushed', False, bool))
        self.settings.endArray()

        tab: ChannelSettingsGUI
        checked_tabs_count: int = sum(tab.isChecked() for tab in self.tabs)
        if checked_tabs_count:
            i: int
            c: pg.PlotItem
            for i, c in enumerate(self.canvases):
                c.setVisible(i < checked_tabs_count)
        self.plot.setVisible(checked_tabs_count)

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
        tab: ChannelSettingsGUI
        tab_index: int = self.tabs_container.indexOf(self.sender())
        for index, tab in enumerate(self.tabs):
            if index == tab_index:
                continue
            if channel == tab.physical_channel:
                tab.setChecked(False)

    def on_tab_toggled(self, on: bool) -> None:
        any_channel_active: bool = any(t.isChecked() for t in self.tabs)
        self.button_start.setEnabled(any_channel_active)

        tab: ChannelSettingsGUI
        checked_tabs_count: int = sum(tab.isChecked() for tab in self.tabs)
        if checked_tabs_count:
            i: int
            c: pg.PlotItem
            for i, c in enumerate(self.canvases):
                c.setVisible(i < checked_tabs_count)
        self.plot.setVisible(checked_tabs_count)

        if not on:
            return

        other_channels: Set[int] = set()
        for tab in self.tabs:
            if tab.isChecked() and tab is not self.sender() and tab.physical_channel is not None:
                other_channels.add(tab.physical_channel)
        self.sender().spin_channel.setValue(min(set(list(range(self.sender().spin_channel.minimum() - 1,
                                                               self.sender().spin_channel.maximum())))
                                                .difference(other_channels)) + 1)

    def on_tab_color_changed(self, color: QColor) -> None:
        for line, tab in zip(self.plot_lines, self.tabs):
            if self.sender() is tab:
                line.setPen(color)


class FileWriter(Process):
    def __init__(self, requests_queue: Queue[Tuple[Optional[Path], FileWritingMode, np.ndarray]]):
        super(Process, self).__init__()

        self.requests_queue: Queue[Tuple[Optional[Path], FileWritingMode, np.ndarray]] = requests_queue

    @property
    def done(self) -> bool:
        return self.requests_queue.empty()

    def run(self) -> None:
        file_path: Optional[Path]
        file_mode: FileWritingMode
        x: np.ndarray
        f_out: TextIO

        while True:
            file_path, file_mode, x = self.requests_queue.get(block=True)
            if file_path is None:
                continue
            with file_path.open(file_mode) as f_out:
                f_out.writelines((('\t'.join(f'{xii}' for xii in xi)
                                   if isinstance(xi, Iterable)
                                   else f'{xi}'
                                   ) + '\n')
                                 for xi in x)


class App(GUI):
    def __init__(self, flags: Qt.WindowFlags = Qt.WindowFlags()) -> None:
        super(App, self).__init__(flags=flags)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

        self.requests_queue: Queue[Tuple[Optional[Path], FileWritingMode, np.ndarray]] = Queue()
        self.results_queue: Queue[np.ndarray] = Queue()
        self.measurement: Optional[Measurement] = None
        self.file_writer: Optional[FileWriter] = None

        self._data: List[np.ndarray] = []

        self._index_map: List[int] = []

    def on_button_start_clicked(self) -> None:
        super(App, self).on_button_start_clicked()
        t: ChannelSettingsGUI
        i: int
        self._index_map = []
        for i, t in enumerate(self.tabs):
            if t.isChecked():
                self._index_map.append(i)
        active_settings: List[ChannelSettingsGUI] = [t for t in self.tabs if t.isChecked()]
        c: pg.PlotItem
        for i, c in enumerate(self.canvases):
            c.clearPlots()
            c.setVisible(i < len(active_settings))
        self.plot_lines = [c.plot(np.empty(0),
                                  name=f'{t.physical_channel}',
                                  pen=t.color_button.color())
                           for c, t in zip(self.canvases, active_settings)]
        self._data = [np.empty(0) for _ in active_settings]
        self.timer.start(10)
        self.measurement = Measurement(self.results_queue,
                                       ip_address=self.text_ip_address.text(),
                                       settings=active_settings,
                                       adc_frequency_divider=self.spin_frequency_divider.value(),
                                       data_portion_size=self.spin_portion_size.value(),
                                       digital_lines=self.digital_lines)
        self.measurement.start()
        self.file_writer = FileWriter(self.requests_queue)
        self.file_writer.start()

    def on_button_stop_clicked(self) -> None:
        if self.measurement is not None:
            self.measurement.terminate()
            self.measurement.join()
        if self.file_writer is not None:
            self.file_writer.terminate()
            self.file_writer.join()
        self.timer.stop()
        super(App, self).on_button_stop_clicked()

    def on_timeout(self) -> None:
        ch: int
        d: np.ndarray
        line: pg.PlotDataItem
        needs_updating: bool = not self.results_queue.empty()
        while not self.results_queue.empty():
            data: np.ndarray = self.results_queue.get()
            for ch, line in zip(range(data.shape[1]), self.plot_lines):
                channel_data: np.ndarray = data[..., ch]
                if not channel_data.size:
                    continue
                self._data[ch] = np.concatenate((self._data[ch], channel_data))
                tab_index: int = self._index_map[ch]
                if self.tabs[tab_index].saving_location.path is not None:
                    self.requests_queue.put((self.tabs[tab_index].saving_location.path,
                                             cast(FileWritingMode, 'at'),
                                             channel_data))
        if needs_updating:
            for d, line in zip(self._data, self.plot_lines):
                line.setData(d)


if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)
    window: App = App()
    window.show()
    app.exec()
