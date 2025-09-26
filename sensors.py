from multiprocessing import Process, Queue
from threading import Event, Thread
from queue import Empty, Full
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
        self.latest_reading = None
        self.latest_reading_queue = Queue(maxsize=1)
        self._latest_thread = None
        self._latest_thread_stop = None
    
    def start_daemon(self):
        print('Starting daemon...')
        self.daemon = Process(target=self.start_loop, args=(self.sampling_buffer, self.daemon_status))
        self.daemon.start()
        self.start_latest_readings_thread()
        print('Daemon started.')
    
    def stop_daemon(self):
        print('Stopping daemon...')
        self.daemon_status.put(1)
        # self.daemon.kill()
        self.daemon.join()
        self.stop_latest_readings_thread()
        print('Daemon stopped.')
    
    def start_latest_readings_thread(self):
        if self._latest_thread and self._latest_thread.is_alive():
            return
        if self._latest_thread_stop is None:
            self._latest_thread_stop = Event()
        else:
            self._latest_thread_stop.clear()
        self._latest_thread = Thread(target=self._latest_readings_worker, daemon=True)
        self._latest_thread.start()

    def stop_latest_readings_thread(self):
        if not self._latest_thread:
            return
        stop_event = self._latest_thread_stop
        if stop_event is not None:
            stop_event.set()
        try:
            self.latest_reading_queue.put_nowait(None)
        except Full:
            try:
                self.latest_reading_queue.get_nowait()
            except Empty:
                pass
            try:
                self.latest_reading_queue.put_nowait(None)
            except Full:
                pass
        if self._latest_thread.is_alive():
            self._latest_thread.join(timeout=2.0)
        self._latest_thread = None

    def _latest_readings_worker(self):
        stop_event = self._latest_thread_stop
        if stop_event is None:
            return
        while not stop_event.is_set():
            try:
                sample = self.latest_reading_queue.get(timeout=1.0)
            except Empty:
                continue
            if sample is None:
                continue
            parsed = self._parse_sample(sample)
            if parsed is not None:
                self.latest_reading = parsed

    def _publish_latest_sample(self, sample: str):
        try:
            self.latest_reading_queue.put_nowait(sample)
        except Full:
            try:
                self.latest_reading_queue.get_nowait()
            except Empty:
                pass
            try:
                self.latest_reading_queue.put_nowait(sample)
            except Full:
                pass

    def _parse_sample(self, sample: str):
        entries = sample.strip().split()
        headers = self.header.strip().split()
        if len(entries) != len(headers):
            return None
        parsed = {}
        for key, value in zip(headers, entries):
            if key == 'timestamp':
                try:
                    parsed[key] = datetime.fromtimestamp(float(value))
                except (ValueError, OSError):
                    parsed[key] = None
            else:
                if value == 'None':
                    parsed[key] = None
                else:
                    try:
                        parsed[key] = float(value)
                    except ValueError:
                        parsed[key] = value
        return parsed

    def get_latest_reading(self):
        if self.latest_reading is None:
            return None
        return self.latest_reading.copy()

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
    
    def start_loop(self, sampling_buffer: Queue, daemon_status: Queue):
        # loop while daemon_status is empty
        while daemon_status.empty():
            fn_dt = datetime.now()
            self.init_file(fn_dt)
            while self.loop_counter < self.reset_threshold:
                self.savefile = open(self.savefile.name, 'a')
                sample = self.read_sensors()
                self.savefile.write(sample)
                sampling_buffer.put(sample)
                self._publish_latest_sample(sample)
                sleep(self.sampling_delay)
                self.savefile.close()
                self.loop_counter += 1
                if daemon_status.empty() == False:
                    break
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