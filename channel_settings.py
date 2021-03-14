# coding: utf-8
from typing import Union, Dict, Optional

try:
    from typing import Final
except ImportError:
    # stub
    class Final:
        @staticmethod
        def __getitem__(item):
            return item


class ChannelSettings:
    """
        Таблица 3.17: Формат настроек логического канала АЦП
        Биты  Обозначение     Доступ  Описание
        2–0   LCH_RANGE       RW       Диапазон измерения для заданного канала:
                                      ’0’ — ±10 В
                                      ’1’ — ±5 В
                                      ’2’ — ±2 В
                                      ’3’ — ±1 В
                                      ’4’ — ±0.5 В
                                      ’5’ — ±0.2 В
                                      ’6’, ’7’ — резерв
        6–3   LCH_CHAN_NUM    RW      Номер физического канала: 0 — 1-ый (17-ый) ка-
                                      нал, 15 — 16-ый (32-ой) канал
        8–7   LCH_CHAN_MODE   RW      Режим измерения:
                                      ’0’ — дифференциальный
                                      ’1’ — первые 16 каналов с общей землей
                                      ’2’ — вторые 16 каналов с общей землей
                                      ’3’ — собственный ноль
        15–9  LCH_AVG         RW      Количество отсчетов для усреднения равно LCH_AVG+1
        31–16 -               -       Резерв
    """

    VOLTAGE_RANGE: Final[Dict[int, float]] = {
        0: 10.,
        1: 5.0,
        2: 2.0,
        3: 1.0,
        4: 0.5,
        5: 0.2
    }

    def __init__(self, data: Optional[Union[bytes, int]] = None):
        self._range: Optional[int] = None
        self._phy_ch: Optional[int] = None
        self._ch_mode: Optional[int] = None
        self._ch_averaging: Optional[int] = None

        if isinstance(data, bytes):
            data = int.from_bytes(data, 'little', signed=False)
        if data is not None:
            self._range = data & 0x7
            self._phy_ch = (data >> 3) & 0xf
            self._ch_mode = (data >> 7) & 0x3
            self._ch_averaging = ((data >> 9) & 0x7f) + 1

    @property
    def range(self) -> int:
        return self._range

    @range.setter
    def range(self, new_value: int):
        if 0 <= new_value <= 5:
            self._range = new_value
        else:
            raise ValueError('Invalid channel range')

    def range_value(self) -> float:
        return self.VOLTAGE_RANGE[self._range]

    @property
    def physical_channel(self) -> int:
        return self._phy_ch

    @physical_channel.setter
    def physical_channel(self, new_value: int):
        if 0 <= new_value <= 15:
            self._phy_ch = new_value
        else:
            raise ValueError('Invalid physical channel number')

    @property
    def mode(self) -> int:
        return self._ch_mode

    @mode.setter
    def mode(self, new_value: int):
        if 0 <= new_value <= 3:
            self._ch_mode = new_value
        else:
            raise ValueError('Invalid channel mode')

    @property
    def averaging(self) -> int:
        return self._ch_averaging

    @averaging.setter
    def averaging(self, new_value: int):
        if 1 <= new_value <= 128:
            self._ch_averaging = new_value
        else:
            raise ValueError('Invalid channel averaging')

    def __int__(self) -> int:
        if self._range is None or self._phy_ch is None or self._ch_mode is None or self._ch_averaging is None:
            raise RuntimeError('Some or all settings are not defined')
        return self._range | (self._phy_ch << 3) | (self._ch_mode << 7) | ((self._ch_averaging - 1) << 9)
