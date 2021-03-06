

# Плагин для [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2)
# Описание
Плагин управляет адресной светодиодной лентой на чипах ws2812.
Проверено на платах Opi pc 3 ядро, opi zero 3 и 4 ядро, opi zero plus 4 ядро, raspberry pi3.

# Подключение 
 сигнальная линия светодиодов подключается к 19 выводу гребенки (должно быть одинаково для всех raspberry совместимых плат) 
 если светодиодов не более 10, то питание можно подать так-же с гребенки
 
# Настройка SPI для 3 ядра Armbian (Orange pi и т.д.)

```
Не требуется 
```  
# Настройка SPI для 4 ядра Armbian (Orange pi Zero, для других Opi скорее всего spi_bus и spi_cs будет 0)

```
в файл  /boot/armbianEnv.txt добавить строки

overlays=w1-gpio i2c0 i2c1 spi-spidev spi-add-cs1
param_spidev_spi_bus=1
param_spidev_spi_cs=1
extraargs=fbcon=map:0 fbcon=font:MINI4x6

Перезагрузить плату
ввести команду ls -l /dev/*spi*
должно появится устройство 
crw------- 1 root root 153, 0 Feb 26 05:29 /dev/spidev1.1
``` 
# Настройка SPI для Raspbian (Raspberry pi)

```
sudo raspi-config
выбрать 
Interfacing Options
далее 
SPI
далее <YES> -> <ok> -> <finish>
ввести команду ls -l /dev/*spi*
должны появится устройства

crw-rw---- 1 root spi 153, 0 Feb 26 11:35 /dev/spidev0.0
crw-rw---- 1 root spi 153, 1 Feb 26 11:35 /dev/spidev0.1

для использования SPI1 (38 контакт), его необходимо включить, для этого нужно добавить строку 
dtoverlay=spi1-3cs в файл /boot/config.txt 
и изменить частоту ядра GPU до 250 МГц, в противном случае  SPI имеет неправильную частоту.
это делается добавлением строки core_freq=250 в указанный файл.
Полле всех страданий нужно перезагрузить плату
``` 
# Установка
 
```
cd ~
git clone https://github.com/doceme/py-spidev.git
cd py-spidev
~/mdmTerminal2/env/bin/python -m setup.py install
cd ~/mdmTerminal2/src/plugins
git clone https://github.com/Flokss/mdmt2-ws2812.git

```

И перезапустить терминал.
```
Запуск без root 

Для плат Orange pi в файл  /etc/rc.local добавить
chmod 777 /dev/spidev1.1

Для платы Raspberry pi достаточно добавить пользователя в группу spi
sudo usermod -a -G spi pi

```

# Настройка
Настройки хранятся в mdmTerminal2/src/data/ws2812_config.json, файл будет создан при первом запуске:
```
spi:[0,0] номер шины SPI 0,0 или 1,0, по умолчанию 0,0 (смотрите вывод ls -l /dev/*spi*) 
(для платы Orange pi zero H2+ c 3 ядром spi:[1,0])
(для платы Orange pi zero H2+ c 4 ядром spi:[1,1])
(для платы Orange pi zero plus H5 c 4 ядром spi:[1,1])
(для платы Orange pi PC H3 c 3 ядром spi:[0,0])
(для платы Raspberry pi c 4 ядром spi:[0,0]) SPI0
(для платы Raspberry pi c 4 ядром spi:[1,0]) SPI1


intensity: максимальная яркость свечения светодиодов (от 0 до 255) по умолчанию 30
num_led: количество светодиодов, по умолчанию 8
```
