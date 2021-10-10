# coding: utf-8

from __future__ import annotations

from multiprocessing import Queue
from pathlib import Path
from typing import List, Optional, Tuple, cast

import numpy as np
import pyqtgraph as pg

from file_writer import FileWriter, FileWritingMode
from gui.channel_settings import ChannelSettings
from gui.gui import GUI
from gui.measurement import Measurement

if pg.Qt.QT_LIB == pg.Qt.PYSIDE6:
    from PySide6.QtCore import QTimer, Qt  # type: ignore
    from PySide6.QtWidgets import QApplication  # type: ignore
elif pg.Qt.QT_LIB == pg.Qt.PYQT5:
    from PyQt5.QtCore import QTimer, Qt  # type: ignore
    from PyQt5.QtWidgets import QApplication  # type: ignore
elif pg.Qt.QT_LIB == pg.Qt.PYSIDE2:
    from PySide2.QtCore import QTimer, Qt  # type: ignore
    from PySide2.QtWidgets import QApplication  # type: ignore

    QApplication.exec = QApplication.exec_
else:
    raise ImportError('PySide6, or PyQt5, or PySide2, is required. PyQt6 is not supported.')


__all__ = ['QApplication', 'App']


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
        t: ChannelSettings
        i: int
        self._index_map = []
        for i, t in enumerate(self.tabs):
            if t.isChecked():
                self._index_map.append(i)
        active_settings: List[ChannelSettings] = [t for t in self.tabs if t.isChecked()]
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
