# coding: utf-8
import socket
import struct
from datetime import datetime
from typing import Union, Tuple, List, Optional, Sequence

import numpy as np

from channel_settings import ChannelSettings
from hardware_info import HardwareInfo
from stubs import Final

__all__ = ['E502', 'X502_ADC_FREQ_DIV_MAX']

X502_ADC_FREQ_DIV_MAX: Final[int] = 1 << 20


class E502:
    def __init__(self, ip: str, verbose: bool = False) -> None:
        self._ip: Final[str] = ip[:]
        self._control_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._control_socket.connect((ip, 11114))
        self._data_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._data_socket.connect((ip, 11115))
        self._settings: List[ChannelSettings] = []
        self._verbose: Final[bool] = verbose

        self._digital_out: List[bool] = [False] * 16
        self._adc_scales: List[float] = []
        self._adc_offsets: List[float] = []
        self._dac_scales: List[float] = []
        self._dac_offsets: List[float] = []

    def __del__(self) -> None:
        self._control_socket.close()
        self._data_socket.close()

    def send_request(self, command: int, parameter: int, payload: Union[bytes, int, bool], response_size: int) -> None:
        if isinstance(payload, bool):
            payload = int(payload)
        if isinstance(payload, int):
            payload = payload.to_bytes(4, 'little')
        if len(payload) > 512:
            raise ValueError('Too large payload')
        if response_size > 512:
            raise ValueError('Too long response')
        self._control_socket.send(b''.join((
            b'CTL1',
            command.to_bytes(4, 'little'),
            parameter.to_bytes(4, 'little'),
            len(payload).to_bytes(4, 'little'),
            response_size.to_bytes(4, 'little'),
            payload,
        )))

    def get_response(self) -> Tuple[bytes, int]:
        ctl1: bytes = self._control_socket.recv(4)
        if self._verbose:
            print(f"CTL1          = {ctl1!r}")
        error: int = int.from_bytes(self._control_socket.recv(4), 'little', signed=True)
        if self._verbose:
            print(f"error         = {error:x}")
        response_size: int = int.from_bytes(self._control_socket.recv(4), 'little')
        if self._verbose:
            print(f"response size = {response_size}")
        response: bytes = self._control_socket.recv(response_size)
        if self._verbose:
            print(f"response      = {response!r}")
        return response, error

    # 0x0200–0x03FF     IO_HARD             Управление вводом-выводом
    # 0x0400–0x04FF     IO_ARITH            Дополнительная обработка

    # Таблица 3.15: Регистры блока управления вводом-выводом (IO_HARD)
    # Адрес (+ 0x200)   Регистр             Доступ  Описание
    # 0x0–0xFF          L TABLE             RW      Таблица настроек логических каналов,определя-
    #                                               ющих последовательность опроса каналов АЦП.
    #                                               Каждый 32-битный регистр задает настройки од-
    #                                               ного логического канала, при этом по адресу 0 на-
    #                                               ходятся настройки последнего логического кана-
    #                                               ла, 1 — предпоследнего, N−1 — первого. Формат
    #                                               настроек приведен в Таблице 3.17.
    # 0x100             LCH_CNT             RW      Задает количество логических каналов в управля-
    #                                               ющей таблице АЦП. Размер логической таблицы равен
    #                                               LCH_CNT+1.
    # 0x102             ADC_FREQ_DIV        RW      Делитель частоты синхронного ввода с АЦП. Ча-
    #                                               стота ввода с АЦП равна f_ref/(ADC_FREQ_DIV+1),
    #                                               где f_ref — опорная частота синхронизации
    # 0x104             ADC_FRAME_DELAY     RW      Значение межкадровой задержки в периодах опорной
    #                                               частоты
    # 0x106             DIGIN_FREQ_DIV      RW      Делитель частоты синхронного ввода с циф-
    #                                               ровых входов. Частота ввода с DIN равна
    #                                               f_ref/(DIGIN_FREQ_DIV+1), где f_ref — опорная ча-
    #                                               стота синхронизации
    # 0x108             IO_MODE             RW      Регистр задает режим синхронизации старта син-
    #                                               хронного ввода и делитель ЦАП. Также при чте-
    #                                               нии может использоваться для проверки захвата
    #                                               частоты синхронизации. Значение битов приведе-
    #                                               но в Таблице 3.18
    # 0x10A             GO_SYNC_IO          W       Запись 1 в этот регистр приводит к запуску син-
    #                                               хронного ввода-вывода, а 0 — к его останову.
    # 0x10C             PRELOAD_ADC         W       Перед записью 1 врегистр GO_SYNC_IO необходи-
    #                                               мовыполнить две записи в этот регистр. По фак-
    #                                               ту записи будет выполнена начальная установка
    #                                               автомата синхронного ввода-вывода и установка
    #                                               коммутации АЦП. Две записине обходимы, так как
    #                                               конвейер автомата управления входной ком-
    #                                               мутации АЦП состоит из 2-х стадий. В противном
    #                                               случае, время момента первого отсчета АЦП мо-
    #                                               жет не совпадать с моментом запуска синхрони-
    #                                               зации
    # 0x112             ASYNC_OUT           W       Асинхронный вывод на цифровые линии или на один
    #                                               из каналов ЦАП. Биты приведены в Таблице 3.19
    # 0x114             LED                 W       Управление красным цветом светодиода на перед-
    #                                               ней панели модуля при остановленном синхрон-н
    #                                               омв воде-выводе (0 — погашен, 1 — горит). При
    #                                               запущенном синхронном вводе-выводе светодиод
    #                                               всегда горит зеленым цветом.
    # 0x116             DIGIN_PULLUP        W       Включение или отключение подтягивающих рези-
    #                                               сторов на цифровых входах. Биты приведены в
    #                                               Таблице 3.20
    # 0x118             OUTSWAP_BFCTL       W       Подкачка отсчета на ЦАП и управления режима-
    #                                               ми SPORT0 для BlackFin. Биты приведены в Таб-
    #                                               лице 3.21

    # Таблица 3.16: Регистры блока дополнительной обработки ввода-вывода (IO_ARITH)
    # Адрес (+ 0x400)   Регистр             Доступ  Описание
    # 0x0               ADC_COEF_B10        W       Коэффициент смещения нуля для диапазона ±10 В
    # 0x1               ADC_COEF_B5         W       Коэффициент смещения нуля для диапазона ±5 В
    # 0x2               ADC_COEF_B2         W       Коэффициент смещения нуля для диапазона ±2 В
    # 0x3               ADC_COEF_B1         W       Коэффициент смещения нуля для диапазона ±1 В
    # 0x4               ADC_COEF_B05        W       Коэффициент смещения нуля для диапазона ±0.5 В
    # 0x5               ADC_COEF_B02        W       Коэффициент смещения нуля для диапазона ±0.2 В
    # 0x8               ADC_COEF_K10        W       Коэффициент шкалы нуля для диапазона ±10 В
    # 0x9               ADC_COEF_K5         W       Коэффициент шкалы нуля для диапазона ±5 В
    # 0xA               ADC_COEF_K2         W       Коэффициент шкалы нуля для диапазона ±2 В
    # 0xB               ADC_COEF_K1         W       Коэффициент шкалы нуля для диапазона ±1 В
    # 0xC               ADC_COEF_K05        W       Коэффициент шкалы нуля для диапазона ±0.5 В
    # 0xD               ADC_COEF_K02        W       Коэффициент шкалы нуля для диапазона ±0.2 В
    # 0x12              ADC_FREQ_DIV        W       Должно быть записано то же значение, что и в
    #                                               аналогичный регистр управления вводом-выводом
    # 0x19              IN_STREAM_ENABLE    W       Разрешение синхронных потоков на ввод (бит 0
    #                                               разрешает ввод с АЦП, бит 1 — с цифровых линий)
    # 0x1A              DIN_ASYNC           W       В данном регистре сохраняется последнее вве-
    #                                               денное значение с цифровых линий при запу-
    #                                               щенном синхронном вводе (GO_SYNC_IO = 1)
    #                                               независимо от разрешения в IN_STREAM_ENABLE.
    #                                               Позволяет эмулировать асинхронный ввод. Би-
    #                                               ты описаны в Таблице 3.22

    def read_register(self, number: int) -> Tuple[bytes, int]:
        self.send_request(0x10, number, bytes(), 4)
        return self.get_response()

    def write_register(self, number: int, payload: Union[bool, int, bytes]) -> int:
        if isinstance(payload, bool):
            payload = int(payload)
        if isinstance(payload, int):
            payload = payload.to_bytes(4, 'little')
        self.send_request(0x11, number, payload, 0)
        return self.get_response()[1]

    def read_int(self, number: int) -> Tuple[int, int]:
        response: Final[Tuple[bytes, int]] = self.read_register(number)
        return int.from_bytes(response[0], 'little'), response[1]

    def read_flash_memory(self, address: int, length: int) -> Tuple[bytes, int]:
        if not (0 < length < 512):
            raise ValueError('Invalid data length to read')
        self.send_request(0x17, address, bytes(), length)
        return self.get_response()

    def write_flash_memory(self, address: int, data: bytes) -> Tuple[bytes, int]:
        if not (0 < len(data) < 512):
            raise ValueError('Invalid data length to write')
        self.send_request(0x18, address, data, 0)
        return self.get_response()

    def start_data_stream(self, as_dac: bool = False) -> int:
        self.send_request(0x12, (1 << 16) if as_dac else 0, bytes(), 0)
        return self.get_response()[1]

    def stop_data_stream(self, as_dac: bool = False) -> int:
        self.send_request(0x13, (1 << 16) if as_dac else 0, bytes(), 0)
        return self.get_response()[1]

    def is_data_stream_running(self, as_dac: bool = False) -> Tuple[bool, int]:
        self.send_request(0x15, (1 << 16) if as_dac else 0, bytes(), 1)
        response: Final[Tuple[bytes, int]] = self.get_response()
        return bool(int.from_bytes(response[0], 'little')), response[1]

    def read_module_data(self) -> Tuple[bytes, int]:
        self.send_request(0x80, 0, bytes(), 192)
        return self.get_response()

    def hardware(self) -> Optional[HardwareInfo]:
        data: bytes
        error: int
        data, error = self.read_register(0x010a)
        if error:
            if self._verbose:
                print('error:', error)
            return None
        else:
            if self._verbose:
                print(HardwareInfo(data))
            return HardwareInfo(data)

    def calibration_data(self) -> None:
        data: bytes
        error: int
        data, error = self.read_flash_memory(0x1F0080, 0xe0)
        if self._verbose and error:
            print('error:', error)
            return
        while data:
            target: int = int.from_bytes(data[12:16], 'little')
            if self._verbose:
                print('for', ['', 'ADC', 'DAC'][target] + ':')
                print('calibration time:', datetime.fromtimestamp(int.from_bytes(data[32:40], 'little')))
            channels_count: int = int.from_bytes(data[40:44], 'little')
            ranges_count: int = int.from_bytes(data[44:48], 'little')
            offset: int = 48
            for r in range(ranges_count):
                for c in range(channels_count):
                    if self._verbose:
                        print(f'for range {r} of channel {c}: ', end='')
                        print(f'offset is', *struct.unpack_from('<d', data, offset), end=', ')
                    if target == 1:
                        self._adc_offsets.extend(struct.unpack_from('<d', data, offset))
                    elif target == 2:
                        self._dac_offsets.extend(struct.unpack_from('<d', data, offset))
                    offset += 8
                    if self._verbose:
                        print(f'scale is', *struct.unpack_from('<d', data, offset))
                    if target == 1:
                        self._adc_scales.extend(struct.unpack_from('<d', data, offset))
                    elif target == 2:
                        self._dac_scales.extend(struct.unpack_from('<d', data, offset))
                    offset += 8
            data = data[offset:]

    def reset_data_socket(self) -> int:
        self.send_request(0x23, 0, bytes(), 0)
        response: Final[int] = self.get_response()[1]
        self._data_socket.close()
        self._data_socket.connect((self._ip, 11115))
        return response

    def read_channels_settings_table(self) -> Tuple[Sequence[ChannelSettings], int]:
        channels_count: int
        error: int
        channels_count, error = self.read_int(0x300)
        channels_settings: List[ChannelSettings] = []
        if error:
            return channels_settings, error
        channel: int
        for channel in range(channels_count + 1):
            channel_settings, error = self.read_int(0x200 + 4 * (channels_count - channel - 1))
            if error:
                return channels_settings, error
            channels_settings.append(ChannelSettings(channel_settings))
        return channels_settings, 0

    def write_channels_settings_table(self, channels_settings: Sequence[ChannelSettings]) -> None:
        self._settings = list(channels_settings)
        self.write_register(0x300, len(channels_settings) - 1)
        channel: int
        channel_settings: ChannelSettings
        for channel, channel_settings in enumerate(channels_settings):
            self.write_register(0x200 + 4 * (len(channels_settings) - channel - 1), int(channel_settings))

    def write_analog(self, index: int, value: float) -> None:
        if not self._dac_scales:
            self.calibration_data()
        if not (0 <= index < len(self._dac_scales)):
            raise ValueError('Invalid analog output')
        payload: bytes = round(value * self._dac_scales[index] * 6000 + self._dac_offsets[index])\
            .to_bytes(2, 'little', signed=True) + b'\0' + [b'\x40', b'\x80'][index]
        self.send_request(
            0x11, 0x312,
            payload,
            0)

    def write_digital(self, index: int, on: bool) -> None:
        if not (0 <= index < len(self._digital_out)):
            raise ValueError('Invalid digital output')
        self._digital_out[index] = on
        self.send_request(
            0x11, 0x312,
            sum((1 << i) for i, v in enumerate(self._digital_out) if v),
            0)

    def preload_adc(self) -> None:
        self.write_register(0x30C, 1)
        self.write_register(0x30C, 1)  # by design, not an error

    def set_sync_io(self, running: bool) -> None:
        self.write_register(0x30A, running)

    def enable_in_stream(self, from_adc: bool = False, from_digital_inputs: bool = False) -> None:
        self.write_register(0x419, int(from_adc) + int(from_digital_inputs) * 2)

    def set_adc_frequency_divider(self, new_value: int) -> None:
        if not (1 <= new_value <= X502_ADC_FREQ_DIV_MAX):
            raise ValueError('Invalid ADC frequency divider')
        self.write_register(0x302, new_value - 1)
        self.write_register(0x412, new_value - 1)

    def set_digital_lines_frequency_divider(self, new_value: int) -> None:
        if new_value <= 0:
            raise ValueError('Invalid digital lines frequency divider')
        self.write_register(0x306, new_value - 1)

    def get_data(self, size: int) -> np.ndarray:
        if size < 0:
            raise ValueError('Invalid data size', size)

        data: bytes = b''
        remaining_count: int = size * np.dtype(np.float32).itemsize * len(self._settings)
        while remaining_count > 0:
            data_piece: bytes = self._data_socket.recv(remaining_count)
            remaining_count -= len(data_piece)
            data += data_piece
        if remaining_count < 0:
            data = data[:remaining_count]
        return np.frombuffer(data, np.float32).reshape((len(self._settings), -1), ).T
