# coding: utf-8

from __future__ import annotations

from datetime import date, timedelta
from multiprocessing import Queue
from pathlib import Path
from typing import List, Optional, Tuple, cast

import numpy as np

from file_writer import FileWriter, FileWritingMode
from gui.channel_settings import ChannelSettings
from gui.gui import GUI
from gui.measurement import Measurement
from gui.pg_qt import *

__all__ = ['App']


class App(GUI):
    def __init__(self) -> None:
        super(App, self).__init__()

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

        self.requests_queue: Queue[Tuple[Optional[Path], FileWritingMode, np.ndarray]] = Queue()
        self.results_queue: Queue[np.ndarray] = Queue()
        self.measurement: Optional[Measurement] = None
        self.file_writer: FileWriter = FileWriter(self.requests_queue)
        self.file_writer.start()

        self._data: List[np.ndarray] = []
        self._index_map: List[int] = []
        self._start_date: date = date.today()
        self._measurement_index: int = 1

    def __del__(self) -> None:
        self.file_writer.terminate()
        self.file_writer.join(1)

    def _saving_location(self, channel: int) -> Path:
        return (self.saving_location.path
                / str(self._start_date.year)
                / str(self._start_date.month)
                / str(self._start_date.day)
                / self.tabs[channel].title()
                / f'imp_{self._measurement_index:06g}.csv')

    def on_button_start_clicked(self) -> None:
        super(App, self).on_button_start_clicked()
        t: ChannelSettings
        i: int
        self._index_map = []
        for i, t in enumerate(self.tabs):
            if t.isChecked():
                self._index_map.append(i)
        active_settings: List[ChannelSettings] = [t for t in self.tabs if t.isChecked()]

        if date.today() != self._start_date:
            self._measurement_index = 1
        self._start_date = date.today()
        while any(self._saving_location(i + 1).exists() for i in range(32)):
            self._measurement_index += 1
        self._data = [np.empty(0) for _ in active_settings]
        self.measurement = Measurement(self.results_queue,
                                       ip_address=self.text_ip_address.text,
                                       settings=active_settings,
                                       adc_frequency_divider=self.spin_frequency_divider.value(),
                                       data_portion_size=self.spin_portion_size.value(),
                                       digital_lines=self.digital_lines,
                                       duration=timedelta(seconds=self.spin_duration.value()))
        self.measurement.start()
        self.timer.start(10)

    def on_button_stop_clicked(self) -> None:
        self.timer.stop()
        if self.measurement is not None:
            self.measurement.terminate()
            self.measurement.join(.1)
        super(App, self).on_button_stop_clicked()

    def on_timeout(self) -> None:
        ch: int
        d: np.ndarray
        while not self.results_queue.empty():
            data: np.ndarray = self.results_queue.get()
            for ch in range(data.shape[1]):
                channel_data: np.ndarray = data[..., ch]
                if not channel_data.size:
                    continue
                self._data[ch] = np.concatenate((self._data[ch], channel_data))
                tab_index: int = self._index_map[ch]
                if self.saving_location.path is not None:
                    self.requests_queue.put((self._saving_location(self.tabs[tab_index].channel),
                                             cast(FileWritingMode, 'at'),
                                             channel_data))
        if self.measurement is not None and not self.measurement.is_alive():
            self.on_button_stop_clicked()
            self.on_button_start_clicked()
