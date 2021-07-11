# coding: utf-8
from configparser import ConfigParser
from threading import Thread, Lock
from typing import List, NamedTuple

import numpy as np

from channel_settings import ChannelSettings
from e502 import E502
from stubs import Final

QueueRecord = NamedTuple('QueueRecord', file_name=str, file_mode=str, y=np.ndarray)


class FileWriter(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.daemon = True

        self.queue: List[QueueRecord] = []
        self.lock: Lock = Lock()
        self.done: bool = False

    def __del__(self):
        self._write_queue()
        self.done = True

    def write_data(self, file_name: str, file_mode: str, y: np.ndarray) -> None:
        with self.lock:
            self.queue.append(QueueRecord(file_name, file_mode, y))

    def _write_queue(self):
        while self.queue:
            with self.lock:
                qr: QueueRecord = self.queue.pop(0)
            with open(qr.file_name, qr.file_mode) as f_out:
                f_out.writelines(f'{y}\n' for y in qr.y)

    def run(self) -> None:
        while not self.done:
            self._write_queue()


if __name__ == '__main__':
    def main():
        config: ConfigParser = ConfigParser(inline_comment_prefixes=('#', ';'),
                                            default_section='general')
        config.read('settings.ini', encoding='utf-8')

        sections = config.sections()

        device: E502 = E502(config.get(config.default_section, 'ip'), verbose=True)
        measurement_duration: Final[float] = config.getfloat(config.default_section, 'продолжительность измерения')
        portion_size: Final[int] = config.getint(config.default_section, 'размер порции данных')

        device.write_analog(0, 0.0)

        settings: List[ChannelSettings] = []
        for section in sections:
            settings.append(ChannelSettings())
            settings[-1].range = config.getint(section, 'диапазон измерения')
            settings[-1].physical_channel = config.getint(section, 'номер физического канала') - 1
            settings[-1].mode = config.getint(section, 'режим измерения')
            settings[-1].averaging = config.getint(section, 'количество отсчётов для усреднения')

        device.write_channels_settings_table(settings)
        device.set_adc_frequency_divider(config.getint(config.default_section, 'делитель частоты синхронного ввода'))
        device.enable_in_stream(from_adc=True)
        device.start_data_stream()
        device.preload_adc()
        device.set_sync_io(True)

        fw = FileWriter()
        fw.start()

        import time

        total_data_length: int = 0
        try:
            while total_data_length / (2e6 * len(sections)) <= measurement_duration:
                data: np.ndarray = device.get_data(portion_size)
                total_data_length += data.shape[0]
                for index, section in enumerate(sections):
                    fw.write_data(section, 'at', data[..., index])
        except KeyboardInterrupt:
            pass
        device.set_sync_io(False)
        device.stop_data_stream()

        while fw.queue:
            time.sleep(0.01)
        fw.done = True


    main()
