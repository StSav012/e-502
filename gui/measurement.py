# coding: utf-8

from __future__ import annotations

from multiprocessing import Process, Queue
from typing import Sequence

import numpy as np

from channel_settings import ChannelSettings
from e502 import E502
from gui.digital_lines import DigitalLines

__all__ = ['Measurement']


class Measurement(Process):
    def __init__(self, results_queue: Queue[np.ndarray],
                 ip_address: str, settings: Sequence[ChannelSettings], adc_frequency_divider: int,
                 data_portion_size: int, digital_lines: DigitalLines) -> None:
        super(Measurement, self).__init__()
        self.results_queue: Queue[np.ndarray] = results_queue

        self.device: E502 = E502(ip_address)
        self.device.write_channels_settings_table(settings)
        self.device.set_adc_frequency_divider(adc_frequency_divider)

        self.data_portion_size: int = data_portion_size
        self.digital_lines: DigitalLines = digital_lines

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
