import socket
from typing import Union, Tuple, Final


class E502:
    def __init__(self, ip: str):
        self._ip: Final[str] = ip[:]
        self._control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._control_socket.connect((ip, 11114))
        self._data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._data_socket.connect((ip, 11115))

    def __del__(self):
        self._control_socket.close()
        self._data_socket.close()

    def send_request(self, command: int, parameter: int, payload: bytes, response_size: int):
        if len(payload) > 512:
            raise ValueError('Too large payload')
        if response_size > 512:
            raise ValueError('Too long response')
        self._control_socket.send(b''.join((
            0x314C5443.to_bytes(4, 'little'),
            command.to_bytes(4, 'little'),
            parameter.to_bytes(4, 'little'),
            len(payload).to_bytes(4, 'little'),
            response_size.to_bytes(4, 'little'),
            payload,
        )))

    def get_response(self) -> Tuple[bytes, int]:
        print(f"0x314C5443    = {int.from_bytes(self._control_socket.recv(4), 'little'):x}")
        error: int = int.from_bytes(self._control_socket.recv(4), 'little')
        print(f"error         = {error:x}")
        response_size: int = int.from_bytes(self._control_socket.recv(4), 'little')
        print(f"response size = {response_size}")
        response: bytes = self._control_socket.recv(response_size)
        print(f"response      = {response}")
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

    # Таблица 3.17: Формат настроек логического канала АЦП
    # Биты  Обозначение     Доступ  Описание
    # 2–0   LCH_RANGER      W       Диапазон измерения для заданного канала:
    #                               ’0’ — ±10 В
    #                               ’1’ — ±5 В
    #                               ’2’ — ±2 В
    #                               ’3’ — ±1 В
    #                               ’4’ — ±0.5 В
    #                               ’5’ — ±0.2 В
    #                               ’6’, ’7’ — резерв
    # 6–3   LCH_CHAN_NUM    RW      Номер физического канала: 0 — 1-ый (17-ый) ка-
    #                               нал, 15 — 16-ый (32-ой) канал
    # 8–7   LCH_CHAN_MODE   RW      Режим измерения:
    #                               ’0’ — дифференциальный
    #                               ’1’ — первые 16 каналов с общей землей
    #                               ’2’ — вторые 16 каналов с общей землей
    #                               ’3’ — собственный ноль
    # 15–9  LCH_AVG         RW      Количество отсчетов для усреднения равно LCH_AVG+1
    # 31–16 -               -       Резерв

    def read_register(self, number: int) -> Tuple[bytes, int]:
        self.send_request(0x10, number, bytes(), 4)
        return self.get_response()

    def write_register(self, number: int, payload: Union[int, bytes]) -> None:
        if isinstance(payload, int):
            payload = payload.to_bytes(4, 'little')
        self.send_request(0x11, number, payload, 0)

    def start_data_stream(self, as_dac: bool = False) -> int:
        self.send_request(0x12, (1 << 16) if as_dac else 0, bytes(), 0)
        return self.get_response()[1]

    def stop_data_stream(self, as_dac: bool = False) -> int:
        self.send_request(0x13, (1 << 16) if as_dac else 0, bytes(), 0)
        return self.get_response()[1]

    def is_data_stream_running(self, as_dac: bool = False) -> Tuple[bool, int]:
        self.send_request(0x15, (1 << 16) if as_dac else 0, bytes(), 1)
        response: Tuple[bytes, int] = self.get_response()
        return bool(int.from_bytes(response[0], 'little')), response[1]

    def read_module_data(self) -> Tuple[bytes, int]:
        self.send_request(0x80, 0, bytes(), 192)
        return self.get_response()

    def reset_data_socket(self) -> int:
        self.send_request(0x23, 0, bytes(), 0)
        response: int = self.get_response()[1]
        self._data_socket.close()
        self._data_socket.connect((self._ip, 11115))
        return response


if __name__ == '__main__':
    device = E502('192.168.1.128')
    # device.read_register(0x280)
    # device.write_register(0x280, 0)
    device.start_data_stream()
    device.is_data_stream_running()
