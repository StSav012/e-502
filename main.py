from channel_settings import ChannelSettings
from e502 import E502

if __name__ == '__main__':
    device = E502('192.168.1.128')
    settings: ChannelSettings = ChannelSettings()
    settings.range = 0
    settings.physical_channel = 0
    settings.mode = 0
    settings.averaging = 1
    device.write_channels_settings_table([settings for _ in range(8)])
    device.set_adc_frequency_divider(1)
    device.enable_in_stream(from_adc=True)
    device.start_data_stream()
    device.preload_adc()
    device.set_sync_io(True)
    try:
        import time

        t0 = time.time()
        for i in range(16):
            device.get_data(1 << 16)
            print(i, (time.time() - t0) / (i + 1) / (1 << 16) / 8)
    except KeyboardInterrupt:
        pass
    device.set_sync_io(False)
    device.stop_data_stream()
