from multiprocessing import Process, Queue
import tkinter as tk
from tkinter import ttk
import serial
from datetime import datetime
from time import sleep
# Raspberry Pi specific libraries below
try:
    import board
    import busio
    import adafruit_bme280, adafruit_pm25
except ModuleNotFoundError:
    pass

class Sensors:
    def __init__(self, data_folder='./data/', serial_port='/dev/ttyS0'):
        self.data_folder = data_folder
        self.loop_counter = 0
        self.reset_threshold = 720 # 1 hour
        self.sampling_delay = 5 # 5 seconds
        self.reset_pin = None
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c)
        self.savefile = None
        try:
            self.uart = serial.Serial(serial_port, baudrate=9600, timeout=None)
            self.pm25 = adafruit_pm25.PM25_UART(self.uart, self.reset_pin)
        except serial.SerialException:
            self.popup('Serial device not found.')
        self.header = 'timestamp temperature humidity pressure pm10_standard pm25_standard pm100_standard pm10_env pm25_env pm100_env particles_03um particles_05um particles_10um particles_25um particles_50um particles_100um\n'
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
        self.file_state = 0
        self.filename = None
        self.sampling_buffer = Queue()
        self.daemon_status = Queue()
    
    def start_daemon(self):
        print('Starting daemon...')
        self.daemon = Process(target=self.start_loop, args=(self.sampling_buffer, self.daemon_status))
        self.daemon.start()
        print('Daemon started.')
    
    def stop_daemon(self):
        print('Stopping daemon...')
        self.daemon_status.put(1)
        self.daemon.kill()
        # self.daemon.join()
        print('Daemon stopped.')
    
    def popup(msg):
        popup = tk.Tk()
        popup.wm_title("!")
        label = ttk.Label(popup, text=msg)
        label.pack(side="top", fill="x", pady=10)
        B1 = ttk.Button(popup, text="OK", command = popup.destroy)
        B1.pack()
        popup.mainloop()

    def read_sensors(self) -> str:
        now = datetime.now()
        temperature = self.bme280.temperature
        humidity = self.bme280.humidity
        pressure = self.bme280.pressure
        try:
            particles = self.pm25.read()
        except RuntimeError:
            particles = self.nan_dict
        particles_packet = ''
        for value in particles.values():
            particles_packet += str(value) + ' '
        particles_packet = particles_packet[:-1]
        packet = f"{now.timestamp()} {round(temperature, 1)} {round(humidity, 1)} {round(pressure, 1)} {particles_packet}\n"
        return packet
    
    def start_loop(self, sampling_buffer, daemon_status):
        ds = daemon_status
        # loop while daemon_status is set to True
        while ds.empty():
            fn_dt = datetime.now()
            self.init_file(fn_dt)
            while self.loop_counter < self.reset_threshold:
                self.savefile = open(self.savefile.name, 'a')
                sample = self.read_sensors()
                self.savefile.write(sample)
                sampling_buffer.put(sample)
                sleep(self.sampling_delay)
                self.savefile.close()
                self.loop_counter += 1
            # empty queue and reset counter once it reaches reset threshold
            for i in range(sampling_buffer.qsize()):
                sampling_buffer.get()
            self.loop_counter = 0

    def init_file(self, dt: datetime):
        filename = self.data_folder + dt.strftime('%Y-%m-%d %H-%M-%S') + '.txt'
        self.savefile = open(filename, 'w')
        self.savefile.write(self.header)
        self.savefile.close()

if __name__ == '__main__':
    from time import sleep
    s = Sensors()
    s.start_daemon()
    print('waiting 30 seconds')
    sleep(30)
    s.stop_daemon()