# coding: utf-8
from __future__ import annotations

import sys
import time
from typing import Tuple, List, Sequence

import numpy as np
from numpy.typing import NDArray

from channel_settings import ChannelSettings
from stubs import Final

__all__ = ['E502', 'X502_ADC_FREQ_DIV_MAX']

X502_ADC_FREQ_DIV_MAX: Final[int] = 1 << 20


class E502:
    def __init__(self, ip: str, verbose: bool = False) -> None:
        print('dummy e-502 is being used', file=sys.stderr)

        self._ip: Final[str] = ip[:]
        self._settings: List[ChannelSettings] = []
        self._verbose: Final[bool] = verbose

        self._digital_out: List[bool] = [False] * 16
        self._adc_scales: List[float] = []
        self._adc_offsets: List[float] = []
        self._dac_scales: List[float] = []
        self._dac_offsets: List[float] = []
        self._is_data_steam_running: bool = False

    def start_data_stream(self, as_dac: bool = False) -> int:
        self._is_data_steam_running = True
        return 0

    def stop_data_stream(self, as_dac: bool = False) -> int:
        self._is_data_steam_running = False
        return 0

    def is_data_stream_running(self, as_dac: bool = False) -> Tuple[bool, int]:
        return self._is_data_steam_running, 0

    def write_channels_settings_table(self, channels_settings: Sequence[ChannelSettings]) -> None:
        self._settings = list(channels_settings)

    def write_analog(self, index: int, value: float) -> None:
        pass

    def write_digital(self, index: int, on: bool) -> None:
        pass

    def preload_adc(self) -> None:
        pass

    def set_sync_io(self, running: bool) -> None:
        pass

    def enable_in_stream(self, from_adc: bool = False, from_digital_inputs: bool = False) -> None:
        pass

    def set_adc_frequency_divider(self, new_value: int) -> None:
        pass

    def set_digital_lines_frequency_divider(self, new_value: int) -> None:
        pass

    def get_data(self, size: int) -> NDArray[np.float64]:
        if size < 0:
            raise ValueError('Invalid data size', size)
        time.sleep(0.5)
        print(f'{size} random numbers')
        return np.random.random((size, len(self._settings)), dtype=np.float64)
