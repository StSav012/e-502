# coding: utf-8

from __future__ import annotations

from datetime import timedelta, datetime
from multiprocessing import Process, Queue
from typing import Sequence, Optional

import numpy as np

from channel_settings import ChannelSettings
try:
    from e502_dummy import E502
except (ImportError, ModuleNotFoundError):
    from e502 import E502
from gui.digital_lines import DigitalLines

__all__ = ['Measurement']


class Measurement(Process):
    def __init__(self, results_queue: Queue[np.ndarray],
                 ip_address: str, settings: Sequence[ChannelSettings], adc_frequency_divider: int,
                 data_portion_size: int, digital_lines: DigitalLines,
                 duration: Optional[timedelta] = None) -> None:
        super(Measurement, self).__init__()
        self.results_queue: Queue[np.ndarray] = results_queue

        self.device: E502 = E502(ip_address)
        self.device.write_channels_settings_table(settings)
        self.device.set_adc_frequency_divider(adc_frequency_divider)

        self.data_portion_size: int = data_portion_size
        self.digital_lines: DigitalLines = digital_lines

        self.duration: Optional[timedelta] = duration

        self._terminating: bool = False

    def terminate(self) -> None:
        self._terminating = True

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

        start_time: datetime = datetime.now()

        while not self._terminating and (self.duration is None or datetime.now() - start_time < self.duration):
            self.results_queue.put(self.device.get_data(self.data_portion_size))
