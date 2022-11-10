from time import time, sleep
from datetime import datetime as dt
from sys import exit
import board
import busio
import serial
import adafruit_bme280, adafruit_pm25
from multiprocessing import Process
import matplotlib.pyplot as plt
from collections import deque

class Environment:
    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c)
        self.reset_pin = None
        self.uart = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=None)
        self.pm25 = adafruit_pm25.PM25_UART(self.uart, self.reset_pin)
        self.hour_reset = 0
        self.nan_dict = {
            'pm10 standard': None,
            'pm25 standard': None,
            'pm100 standard': None,
            'pm10 env': None,
            'pm25 env': None,
            'pm100 env': None,
            'particles 03um': None,
            'particles 05um': None,
            'particles 10um': None,
            'particles 25um': None,
            'particles 50um': None,
            'particles 100 um': None
            }

    def measure(self):
        while True:
            try:
                file = open(f"data/{dt.fromtimestamp(time()).strftime('%Y-%m-%d %H-%M-%S')}.txt", 'a')
                file.write('timestamp temperature humidity pressure pm10_standard pm25_standard pm100_standard pm10_env pm25_env pm100_env particles_03um particles_05um particles_10um particles_25um particles_50um particles_100um\n')
                while self.hour_reset <720:
                    timestamp = time()
                    temperature = self.bme280.temperature
                    humidity = self.bme280.humidity
                    pressure = self.bme280.pressure
                    try:
                        particles = self.pm25.read()
                    except RuntimeError:
                        particles = self.nan_dict
                    file.write(f'{timestamp} {temperature} {humidity} {pressure} ')
                    for i in particles.values():
                        file.write(f'{i} ')
                    file.write('\n')
                    print(f"timestamp: {dt.fromtimestamp(timestamp).strftime('%d-%b-%Y %H:%M:%S')}\ntemperature: {temperature:.2f} C\nhumidity: {humidity:.2f} %RH\npressure: {pressure:.1f} mbar\n")
                    sleep(5)
                    self.hour_reset += 1
                file.close()
                self.hour_reset = 0
            except KeyboardInterrupt:
                file.close()
                print('Shutting down.\n')
                exit()

if __name__ == '__main__':
    em = Environment()
    em_process = Process(target=em.measure)
    em_process.start()

# i2c = busio.I2C(board.SCL, board.SDA)
# bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# reset_pin = None
# uart = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=None)
# pm25 = adafruit_pm25.PM25_UART(uart, reset_pin)

# hour_reset = 0

# while True:
#     try:
#         file = open(f"data/{dt.fromtimestamp(time()).strftime('%Y-%m-%d %H-%M-%S')}.txt", 'a')
#         file.write('timestamp temperature humidity pressure pm10_standard pm25_standard pm100_standard pm10_env pm25_env pm100_env particles_03um particles_05um particles_10um particles_25um particles_50um particles_100um\n')
#         while hour_reset <720:
#             timestamp = time()
#             temperature = bme280.temperature
#             humidity = bme280.humidity
#             pressure = bme280.pressure
#             try:
#                 particles = pm25.read()
#             except RuntimeError:
#                 sleep(1)
#                 particles = pm25.read()
#             file.write(f'{timestamp} {temperature} {humidity} {pressure} ')
#             for i in particles.values():
#                 file.write(f'{i} ')
#             file.write('\n')
#             sleep(5)
#             hour_reset += 1
#         file.close()
#         hour_reset = 0
#     except KeyboardInterrupt:
#         file.close()
#         print('Shutting down.\n')
#         exit()
