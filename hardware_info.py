# coding: utf-8
from typing import Tuple, Optional


class HardwareInfo:
    def __init__(self, data: bytes = bytes()):
        self._has_dac: Optional[bool] = None
        self._has_galvanic_decoupling: Optional[bool] = None
        self._has_black_fin: Optional[bool] = None
        self._plda_version: Optional[int] = None
        self._board_revision: Optional[int] = None
        self._fpga_version: Optional[Tuple[int, int]] = None
        self.fill_from_bytes(data)

    def fill_from_bytes(self, data: bytes):
        if not isinstance(data, bytes):
            raise TypeError('The data should be bytes')
        if len(data) == 4:
            self._has_dac = bool(data[0] & 1)
            self._has_galvanic_decoupling = bool(data[0] & 2)
            self._has_black_fin = bool(data[0] & 4)
            self._plda_version = data[0] >> 4
            self._board_revision = data[1] & 0x0f
            self._fpga_version = data[3], data[2]
        elif data:
            self._has_dac = None
            self._has_galvanic_decoupling = None
            self._has_black_fin = None
            self._plda_version = None
            self._board_revision = None
            self._fpga_version = None
            raise ValueError('Incorrect hardware data')

    def __repr__(self) -> str:
        return '\n'.join((
            'DAC is' + '' if self._has_dac else ' not' + ' present',
            'Galvanic decoupling is' + '' if self._has_galvanic_decoupling else ' not' + ' present',
            'BlackFin is' + '' if self._has_black_fin else ' not' + ' present',
            'PLDA version:', self._plda_version,
            'Board revision:', self._board_revision,
            f'FPGA version: {self._fpga_version[0]}.{self._fpga_version[1]}',
        ))

    def __str__(self) -> str:
        return '-'.join((
            'XP'[self._has_black_fin],
            'EU',
            'XD'[self._has_dac]
        ))

    @property
    def has_dac(self) -> Optional[bool]:
        return self._has_dac

    @property
    def has_galvanic_decoupling(self) -> Optional[bool]:
        return self._has_galvanic_decoupling

    @property
    def has_black_fin(self) -> Optional[bool]:
        return self._has_black_fin

    @property
    def plda_version(self) -> Optional[int]:
        return self._plda_version

    @property
    def board_revision(self) -> Optional[int]:
        return self._board_revision

    @property
    def fpga_version(self) -> Optional[Tuple[int, int]]:
        return self._fpga_version
