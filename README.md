# mdmt2-ws2812
# Плагин для [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2)
для работы плагина необходимо чтобы  [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2) запускался с root правами
# Подключение 
 сигнальная линия светодиодов подключается к 19 выводу гребенки (должно быть одинаково для всех raspberry совместимых плат) 
# Установка
Для работы необходимо включить и настроить [SPI шину](https://micro-pi.ru/включение-шины-spi-на-orange-pi/) 
В образе Armbian_5.59_Orangepizero_Ubuntu_xenial_default_3.4.113 все включено и настроено
```
cd ~
git clone https://github.com/doceme/py-spidev.git
cd py-spidev
~/mdmTerminal2/env/bin/python -m setup.py install
cd ~/mdmTerminal2/src/plugins
git clone https://github.com/Flokss/mdmt2-ws2812.git

```
И перезапустить терминал.
# Описание
Плагин управляет адресной светодиодной лентой на чипах ws2812

# Настройка
Настройки хранятся в mdmTerminal2/src/data/ws2812_config.json, файл будет создан при первом запуске:
```
spi: номер шины SPI 0 или 1, по умолчанию 0 (для платы orange pi zero H2+ установить 1, для других скорее всего 0)
intensity: максимальная яркость свечения светодиодов (от 0 до 255) по умолчанию 30
num_led: количество светодиодов, по умолчанию 8
```
