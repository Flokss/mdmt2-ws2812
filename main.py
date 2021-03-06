
import queue
import threading
import time
import random
import spidev
from typing import Any

NAME = 'ws2812'
API = 30
SETTINGS = 'ws2812_config'
spi = spidev.SpiDev()

class Main(threading.Thread):
    _old_volume = 0
    _old_s_volume = 0
    """
    Обязательно. Точка входа в плагин, должна быть callable.
    Ожидается что это объект класса, экземпляр которого будет создан, но может быть и методом.
    Должен принять 3 аргумента, вызов: Main(cfg=self.cfg, log=self._get_log(name), owner=self.own)
    Может содержать служебные методы и свойства, все они опциональны. Методы должны быть строго callable:
    Методы: start, reload, stop, join.
    Свойства: disable.
    """

    def __init__(self, cfg, log, owner):
        """
        Конструктор плагина.
        :param cfg: ссылка на экземпляр config.ConfigHandler.
        :param log: ссылка на специальный логгер, вызов: log(msg, lvl=logger.Debug)
        :param owner: ссылка на экземпляр loader.Loader
        """
        super().__init__()
        global spi_d
        global spi_sd
        global m_intensity
        global n_led
        self.cfg = cfg
        self.log = log
        self.own = owner
        self._queue = queue.Queue()
        self._work = False
        self._settings = self._get_settings()
        spi_d = self._settings['spi'][0]
        spi_sd = self._settings['spi'][1]
        m_intensity = self._settings['intensity']
        self.stat_pl = False
        n_led = self._settings['num_led']
        self._events = ( 'start_record', 'stop_record', 'start_talking', 'stop_talking',
            'volume', 'music_volume','music_status'
        )
        self.disable = False

    @staticmethod
    def _init():
        spi.open(spi_d, spi_sd)

    def _led_off(self):
        self.write2812(spi, [[0, 0, 0]]*n_led)

    def _talking(self, spi):
        step_time = 0.1
        i_step = 0
        while self.stat_pl:
            for ld in range(n_led):
                d = [[0, 0, 0]] * n_led
                d[i_step % n_led] = [m_intensity] * random.randint(1, 4)
                self.write2812(spi, d)
                i_step = (i_step + 1) % n_led
                time.sleep(step_time)
            time.sleep(step_time)
        self._led_off()

    def _record(self, spi):
        step_time = 0.01
        while self.stat_pl:
            for ld in range(m_intensity):
                d = [[0, 0, ld]] * n_led
                self.write2812(spi, d)
                time.sleep(step_time)
            for ld in range(m_intensity,0,-1):
                d = [[0, 0, ld]] * n_led
                self.write2812(spi, d)
                time.sleep(step_time)   

    def _m_volume(self, spi, vol):
        step_time = 0.2

        l_cnt = round(vol/(100/n_led))
        old_l_cnt = round(self._old_volume / (100 / n_led))
        if self._old_volume > vol: # vol -
            d = ([[0, m_intensity, 0]] * old_l_cnt) + ([[0, 0, 0]] * (n_led - old_l_cnt))
            self.write2812(spi, d)
            time.sleep(step_time * 3)
            for ld in range(old_l_cnt, l_cnt, -1):
                d[ld-1] = [0, 0, 0]
                self.write2812(spi, d)
                time.sleep(step_time)
            time.sleep(step_time * 3)
            self._led_off()
        else: # vol +
            d = ([[0, m_intensity, 0]] * old_l_cnt) + ([[0, 0, 0]] * (n_led - old_l_cnt))
            self.write2812(spi, d)
            time.sleep(step_time * 3)
            for ld in range( old_l_cnt, l_cnt, 1):
                d[ld] = [0, m_intensity, 0]
                self.write2812(spi, d)
                time.sleep(step_time)
            time.sleep(step_time * 3)
            self._led_off()
        self._old_volume=vol

    def _s_volume(self, spi, vol):
        step_time = 0.2

        l_cnt = round(vol / (100 / n_led))
        old_l_cnt = round(self._old_s_volume / (100 / n_led))
        if self._old_s_volume > vol:  # vol -
            d = ([[0, m_intensity, m_intensity]] * old_l_cnt) + ([[0, 0, 0]] * (n_led - old_l_cnt))
            self.write2812(spi, d)
            time.sleep(step_time * 3)
            for ld in range(old_l_cnt, l_cnt, -1):
                d[ld - 1] = [0, 0, 0]
                self.write2812(spi, d)
                time.sleep(step_time)
            time.sleep(step_time * 3)
            self._led_off()
        else:  # vol +
            d = ([[0, m_intensity, m_intensity]] * old_l_cnt) + ([[0, 0, 0]] * (n_led - old_l_cnt))
            self.write2812(spi, d)
            time.sleep(step_time * 3)
            for ld in range(old_l_cnt, l_cnt, 1):
                d[ld] = [0, m_intensity, m_intensity]
                self.write2812(spi, d)
                time.sleep(step_time)
            time.sleep(step_time * 3)
            self._led_off()
        self._old_s_volume = vol

    def start(self):
        self._init()
        self._led_off()
        self.own.subscribe(self._events, self._callback)
        self._work = True
        super().start()

    def join(self, timeout=30):
        if self._work:
            self._work = False
            self.stat_pl=False
            self._queue.put_nowait(None)
            super().join(timeout)
        self.own.unsubscribe(self._events, self._callback)
        self._led_off()

    def run(self):
        while self._work:
            cmd = self._queue.get()
            if not cmd:
                continue
            self._processing(cmd)

    def _callback(self, name, data=None, *_, **__):
        self.stat_pl=False
        kwargs = {'name': name, 'data': data}
        self._queue.put_nowait(kwargs)
        
    def _processing(self, cmd):
        if cmd['name'] == 'start_talking':
            self.stat_pl=True
            self._talking(spi)
        elif cmd['name'] == 'music_volume':
            self._m_volume(spi,cmd['data'])
        elif cmd['name'] == 'volume':
            self._s_volume(spi,cmd['data'])
        elif cmd['name'] == 'start_record':
            self.stat_pl=True
            self._record(spi)
        elif cmd['name'] in ('stop_talking', 'stop_record'):
            self._led_off()
        else:
            return
        self.log(cmd['name'])

    def _get_settings(self) -> dict:
        def_cfg = {'spi': [0, 0],  'num_led': 8, 'intensity': 30}
        cfg = self.cfg.load_dict(SETTINGS)
        if isinstance(cfg, dict):
            is_ok = True
            for key, val in def_cfg.items():
                if key not in cfg or not isinstance(cfg[key], type(val)):
                    is_ok = False
                    break
            if is_ok:
                return cfg
        self.cfg.save_dict(SETTINGS, def_cfg, True)
        return def_cfg

    def write2812(self, spi, data):
        tx = [0x00]
        for rgb in data:
            for byte in rgb:
                for ibit in range(3, -1, -1):
                    tx.append(((byte >> (2 * ibit + 1)) & 1) * 0x60 +
                              ((byte >> (2 * ibit + 0)) & 1) * 0x06 +
                              0x88)
        spi.xfer(tx, int(4 / 1.05e-6))
