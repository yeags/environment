from multiprocessing import Process, Queue
from datetime import datetime
from time import time, sleep
import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import os, re
# Raspberry Pi specific libraries below
try:
    import board
    import busio
    import adafruit_bme280, adafruit_pm25
except ModuleNotFoundError:
    pass

class Monitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.timestamp_delta = {'1h': 720, '8h': 5760, '24h': 17280, '7d': 120960,
                                '1m': 518400, '6m': 3110400, '1y': 6307200}
        self.title('Environment Monitor')
        self.geometry('1280x1024')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.root_frame = tk.Frame(self)
        self.root_frame.config(bg='white')
        self.root_frame.columnconfigure(0, weight=1)
        self.root_frame.rowconfigure(0, weight=1)
        self.root_frame.grid(row=0, column=0, sticky='nsew')
        self.create_thp_plot()
        self.create_pms_plot()
        self.create_toolbar()
    
    def __lsdir__(self):
        pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.txt')
        files = os.listdir('./data')
        data_fn = re.findall(pattern, ' '.join(files))
        return data_fn
    
    def close_app(self):
        self.destroy()
    
    def create_thp_plot(self):
        self.thp_figure = thpFigure(self.root_frame)
        self.thp_figure.grid(row=0, column=0, sticky='nsew')

    def create_pms_plot(self):
        self.pms_figure = pmsFigure(self.root_frame)
        self.pms_figure.grid(row=1, column=0, sticky='nsew')
    
    def create_toolbar(self):
        self.toolbar = tk.Frame(self.root_frame, bg='white')
        self.status_bar = ttk.Label(self.toolbar, text='*Status Window*',
            relief='sunken', width=40)
        btn_realtime = ttk.Button(self.toolbar, text='Real-time', command=self.realtime)
        btn_1hr = ttk.Button(self.toolbar, text='1 Hour', command=lambda: self.refresh_plots('1h'))
        btn_8hr = ttk.Button(self.toolbar, text='8 Hours', command=lambda: self.refresh_plots('8h'))
        btn_24hr = ttk.Button(self.toolbar, text='24 Hours', command=lambda: self.refresh_plots('24h'))
        btn_7days = ttk.Button(self.toolbar, text='7 Days', command=lambda: self.refresh_plots('7d'))
        btn_1month = ttk.Button(self.toolbar, text='1 Month', command=lambda: self.refresh_plots('1m'))
        btn_6month = ttk.Button(self.toolbar, text='6 Month', command=lambda: self.refresh_plots('6m'))
        btn_1year = ttk.Button(self.toolbar, text='1 Year', command=lambda: self.refresh_plots('1y'))
        btn_exit = ttk.Button(self.toolbar, text='Exit', command=self.close_app)
        self.status_bar.grid(row=0, column=0, sticky='ew')
        btn_realtime.grid(row=0, column=1, padx=(10,5), sticky='w')
        btn_1hr.grid(row=0, column=2, padx=5, sticky='w')
        btn_8hr.grid(row=0, column=3, padx=5, sticky='w')
        btn_24hr.grid(row=0, column=4, padx=5, sticky='w')
        btn_7days.grid(row=0, column=5, padx=5, sticky='w')
        btn_1month.grid(row=0, column=6, padx=5, sticky='w')
        btn_6month.grid(row=0, column=7, padx=5, sticky='w')
        btn_1year.grid(row=0, column=8, padx=5, sticky='w')
        btn_exit.grid(row=0, column=9, padx=5, sticky='e')
        self.toolbar.grid(row=2, column=0, sticky='ew')
    
    def refresh_plots(self, time_window: str):
        pass
    
    def realtime(self):
        pass


class thpFigure(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # self.screen_dpi = 86
        self.screen_dpi = 94
        self.config(bg='white')
        self.create_figure()
        self.thp_plot.get_tk_widget().grid(row=0, column=0, sticky='nsew')
    
    def create_figure(self):
        self.fig, (self.th, self.p) = plt.subplots(nrows=2, ncols=1, sharex=True,
            figsize=(1280 / self.screen_dpi, 500 / self.screen_dpi),
            dpi=self.screen_dpi)
        self.thp_plot = FigureCanvasTkAgg(self.fig, master=self)
        th2 = self.th.twinx()
        # Configure subplots
        self.th.set_title('Temperature | Humidity')
        self.th.set_ylabel('Temperature [$^\circ$C]', color='C0')
        self.p.set_xlabel('Date', loc='left')
        th2.set_ylabel('Humidity [%RH]', color='C1')
        self.th.grid()
        self.p.set_title('Pressure')
        self.p.set_ylabel('Pressure [mBar]', color='C2')
        self.p.grid()
        self.thp_plot.draw()
    
    def update_plot(self, data):
        pass

class pmsFigure(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.particle_sizes = ['0.3', '0.5', '1.0', '2.5', '5.0', '10.0']
        # self.screen_dpi = 86
        self.screen_dpi = 94
        self.config(bg='white')
        self.create_figure()
        self.pms_plot.get_tk_widget().grid(row=0, column=0, sticky='nsew')
    
    def create_figure(self):
        self.fig, (self.pms_concentration, self.pms_counts) = plt.subplots(nrows=1, ncols=2,
            figsize=(1280 / self.screen_dpi, 500 / self.screen_dpi),
            dpi=self.screen_dpi)
        self.pms_plot = FigureCanvasTkAgg(self.fig, master=self)
        concentration, counts = self.generate_data()
        self.pms_concentration.bar(concentration.keys(), concentration.values())
        self.pms_counts.bar(counts.keys(), counts.values())
        self.pms_concentration.set_title('Particle Concentration')
        self.pms_concentration.set_ylabel('$\mu$g/m$^3$')
        self.pms_concentration.set_xlabel('Particle Size [$\mu$m]')
        self.pms_counts.set_title('Particle Counts')
        self.pms_counts.set_yscale('log')
        self.pms_counts.set_ylabel('Quantity')
        self.pms_counts.set_xlabel('Particle Size [$\mu$m]')
        self.fig.subplots_adjust(bottom=0.1, top=0.95)
        self.pms_plot.draw()
    
    def update_plot(self, data):
        pass

    def generate_data(self):
        """
        This function is for sandboxing only.  Will be removed in the future.
        """
        concentration = {'1.0': 234, '2.5': 45, '10.0': 22}
        counts = dict(zip(self.particle_sizes, [2500, 855, 127, 50, 8, 2]))
        return (concentration, counts)

class ReadArchive:
    def __init__(self):
        self.timespan_dict = {'1hr': slice(1, 1+1), '8hr': slice(1, 8+1), '24hr': slice(1, 24+1), '7d': slice(1, 168+1),
                              '1m': slice(1, 720+1), '6m': slice(1, 4380+1), '1y': slice(1, 8760+1)}
        self.fn_format = '%Y-%m-%d %H-%M-%S'
        self.re_compile = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}')

    def read_files(self):
        files = os.listdir('./data')
        files_str = ' '.join(files)
        fn_list = re.findall(self.re_compile, files_str)
        fn_timestamp = []
        for fn in fn_list:
            fn_timestamp.append(datetime.strptime(fn, self.fn_format).timestamp())
        self.fn_dict = dict(zip(fn_timestamp, fn_list))
        self.timestamp_list = fn_timestamp.sort(reverse=True)
    
    def load_data(self, timespan = '1hr'):
        data_fn = self.timestamp_list[self.timespan_dict[timespan]]
        data_fn.sort()
        contents_list = []
        for file in data_fn:
            with open('./data/'+file+'.txt') as f:
                f.readline()
                contents_list.append(f.read())
        if len(contents_list) > 1:
            contents = '\n'.join(contents_list)
        else:
            contents = contents_list[0]

class Sensors:
    def __init__(self):
        self.loop_counter = 0
        self.reset_threshold = 720
        self.sampling_delay = 5
        self.reset_pin = None
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c)
        self.reset_pin = None
        self.savefile = None
        try:
            self.uart = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=None)
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
        self.daemon_status = True
        self.mp_queue = Queue()
        self.daemon = Process(target=self.start_loop)
        self.daemon.start()
    
    def popup(msg):
        popup = tk.Tk()
        popup.wm_title("!")
        label = ttk.Label(popup, text=msg)
        label.pack(side="top", fill="x", pady=10)
        B1 = ttk.Button(popup, text="OK", command = popup.destroy)
        B1.pack()
        popup.mainloop()

    def read_sensors(self):
        now = datetime.now()
        # timestamp = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
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
    
    def start_loop(self):
        # loop while daemon_status is set to True
        while self.daemon_status:
            fn_dt = datetime.now()
            self.init_file(fn_dt)
            while self.loop_counter < self.reset_threshold:
                self.savefile = open(self.savefile.name, 'a')
                sample = self.read_sensors()
                self.savefile.write(sample)
                self.mp_queue.put(sample)
                sleep(self.sampling_delay)
                self.savefile.close()
                self.loop_counter += 1
            # empty queue and reset counter once it reaches reset threshold
            for i in range(self.mp_queue.qsize()):
                self.mp_queue.get()
            self.loop_counter = 0

    def init_file(self, dt: datetime):
        filename = dt.strftime('%Y-%m-%d %H-%M-%S') + '.txt'
        self.savefile = open(filename, 'w')
        self.savefile.write(self.header)
        self.savefile.close()

if __name__ == '__main__':
    test = Monitor()
    test.mainloop()