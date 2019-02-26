"""
Технически, плагины являются модулями и мало чем отличаются от базовых систем загружаемых в loader.py,
но т.к. "модули" уже заняты - пусть будут плагины. Основные отличия плагинов:
- Хранятся в директории src/plugins/, содержимое которой занесено в .gitignore терминала.
- Загружаются и запускаются динамически после запуска всех базовых систем терминала. Первыми завершают свою работу.
- Терминал никак не зависит от плагинов.

Путь до плагина выглядит как mdmTerminal2/src/plugins/folder/main.py, где:
folder - директория с плагином, ее имя не имеет значения.
main.py - динамически загружаемый файл модуля. Терминал игнорирует остальные файлы и никак их не использует.

Для успешной инициализации плагина, main.py должен содержать определенные свойства и точку входа (Main).
"""
import queue
import threading
import time

import spidev

"""
Обязательно. Не пустое имя плагина, тип - str.
Максимальная длинна 30 символов, не должно содержать пробельных символов, запятых и быть строго в нижнем регистре.
Имя плагина является его идентификатором и должно быть уникально.
"""
NAME = 'ws2812'


"""
Обязательно. Версия API под которую написан плагин, тип - int.
Если оно меньше config.ConfigHandler.API то плагин не будет загружен, а в лог будет выдано сообщение.
API терминала увеличивается когда публичные методы, их вызов или результат вызова (у cfg, log, owner) изменяется.
API не увеличивается при добавлении новых методов.
Призван защитить терминал от неправильной работы плагинов.
Если API не используется или вам все равно, можно задать заведомо большое число (999999).
"""
API = 30


SETTINGS = 'ws2812_config'
spi = spidev.SpiDev()


class Main(threading.Thread):
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
        n_led = self._settings['num_led']
        self._events = ('start_record', 'stop_record', 'start_talking', 'stop_talking')
        self.disable = False

    @staticmethod
    def _init():
        spi.open(spi_d, spi_sd)

    def _led_off(self):
        # switch all nLED chips OFF.
        self.write2812(spi, [[0, 0, 0]]*n_led)

    def _talking(self, spi):
        step_time = 0.1
        i_step = 0
        for ld in range(n_led):
            d = [[0, 0, 0]] * n_led
            d[i_step % n_led] = [m_intensity] * 3
            self.write2812(spi, d)
            i_step = (i_step + 1) % n_led
            time.sleep(step_time)
        self._led_off()

    def _record(self, spi):
        step_time = 0.01
        for ld in range(m_intensity):
            d = [[0, 0, ld]] * n_led
            self.write2812(spi, d)
            time.sleep(step_time)

    def start(self):
        self._init()
        self._led_off()
        self.own.subscribe(self._events, self._callback)
        self._work = True
        super().start()

    def join(self, timeout=30):
        if self._work:
            self._work = False
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

    def _callback(self, name, *_, **__):
        self._queue.put_nowait(name)

    def _processing(self, name):
        if name == 'start_talking':
            self._talking(spi)
        elif name == 'start_record':
            self._record(spi)
        elif name in ('stop_talking', 'stop_record'):
            self._led_off()
        else:
            return
        self.log(name)

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
        # print [hex(v) for v in tx]
        spi.xfer(tx, int(4 / 1.05e-6))
