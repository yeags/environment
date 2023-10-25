import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from archive import ReadArchive
from sensors import Sensors
import sys, os
from multiprocessing import Process, Queue
from threading import Thread
from datetime import datetime
from dateutil.relativedelta import relativedelta
from time import sleep
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FixedLocator
from matplotlib.transforms import Bbox

class Monitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.archive = ReadArchive()
        self.sensor_active = False
        self.realtime_active = Queue()
        if 'board' in sys.modules:
            self.sensor_active = True
            self.sensor_daemon = Sensors()
            self.sensor_daemon.start_daemon()
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
    
    def close_app(self):
        if self.sensor_active:
            self.sensor_daemon.stop_daemon()
            # try:
            #     self.stop_realtime_process()
            # except:
            #     pass
        self.destroy()
        sys.exit()

    def create_thp_plot(self):
        self.thp_figure = thpFigure(self.root_frame)
        self.thp_figure.grid(row=0, column=0, sticky='nsew')

    def create_pms_plot(self):
        self.pms_figure = pmsFigure(self.root_frame)
        self.pms_figure.grid(row=1, column=0, sticky='nsew')
    
    def refresh_plots_thread(self, time_range):
        self.progress_bar.start()
        self.status_bar.config(text='Refreshing plots...')
        self.refresh_plots(time_range)
        self.status_bar.config(text='*Status Window*')
        self.progress_bar.stop()
    
    def refresh_daterange_plots_thread(self, daterange_files):
        self.progress_bar.start()
        self.status_bar.config(text='Refreshing plots...')
        self.refresh_daterange_plots(daterange_files)
        self.status_bar.config(text='*Status Window*')
        self.progress_bar.stop()

    
    def create_toolbar(self):
        self.toolbar = tk.Frame(self.root_frame, bg='white')
        self.status_bar = ttk.Label(self.toolbar, text='*Status Window*',
            relief='sunken', width=40)
        self.progress_bar = ttk.Progressbar(self.toolbar, orient='horizontal', mode='indeterminate', length=200)
        btn_realtime = ttk.Button(self.toolbar, text='Real-time', command=self.start_realtime_process, state='disabled') # Re-enable once realtime is implemented
        btn_daterange = ttk.Button(self.toolbar, text='Date Range', command=self.get_daterange, state='enabled')
        btn_1hr = ttk.Button(self.toolbar, text='1 Hour', command=lambda: Thread(target=self.refresh_plots_thread, args=('1h',)).start())
        btn_8hr = ttk.Button(self.toolbar, text='8 Hours', command=lambda: Thread(target=self.refresh_plots_thread, args=('8h',)).start())
        btn_24hr = ttk.Button(self.toolbar, text='24 Hours', command=lambda: Thread(target=self.refresh_plots_thread, args=('24h',)).start())
        btn_7days = ttk.Button(self.toolbar, text='7 Days', command=lambda: Thread(target=self.refresh_plots_thread, args=('7d',)).start())
        btn_1month = ttk.Button(self.toolbar, text='1 Month', command=lambda: Thread(target=self.refresh_plots_thread, args=('1m',)).start())
        btn_6month = ttk.Button(self.toolbar, text='6 Month', command=lambda: Thread(target=self.refresh_plots_thread, args=('6m',)).start())
        btn_1year = ttk.Button(self.toolbar, text='1 Year', command=lambda: Thread(target=self.refresh_plots_thread, args=('1y',)).start())
        btn_exit = ttk.Button(self.toolbar, text='Exit', command=self.close_app)
        # self.status_bar.grid(row=0, column=0, sticky='ew')
        self.progress_bar.grid(row=0, column=0, sticky='ew')
        btn_realtime.grid(row=0, column=1, padx=(10,5), sticky='w')
        btn_daterange.grid(row=0, column=2, padx=5, sticky='w')
        btn_1hr.grid(row=0, column=3, padx=5, sticky='w')
        btn_8hr.grid(row=0, column=4, padx=5, sticky='w')
        btn_24hr.grid(row=0, column=5, padx=5, sticky='w')
        btn_7days.grid(row=0, column=6, padx=5, sticky='w')
        btn_1month.grid(row=0, column=7, padx=5, sticky='w')
        btn_6month.grid(row=0, column=8, padx=5, sticky='w')
        btn_1year.grid(row=0, column=9, padx=5, sticky='w')
        btn_exit.grid(row=0, column=10, padx=5, sticky='e')
        self.toolbar.grid(row=2, column=0, sticky='ew')
    
    def get_daterange(self):
        current_date = datetime.now()
        back_date = current_date - relativedelta(months=1)
        top = tk.Toplevel(self)
        top.title('Date Range')
        lbl_start_date = ttk.Label(top, text='From: ')
        lbl_end_date = ttk.Label(top, text='To: ')
        cal_start_date = DateEntry(top, width=12, background='darkblue',
                                   foreground='white', borderwidth=2,
                                   year=back_date.year, month=back_date.month,
                                   day=back_date.day)
        cal_end_date = DateEntry(top, width=12, background='darkblue',
                                 foreground='white', borderwidth=2,
                                 year=current_date.year, month=current_date.month,
                                 day=current_date.day)
        btn_ok = ttk.Button(top, text='OK', command=lambda: Thread(target=on_closing).start())
        lbl_start_date.grid(row=0, column=0, padx=5, pady=5)
        lbl_end_date.grid(row=0, column=2, padx=5, pady=5)
        cal_start_date.grid(row=0, column=1, padx=5, pady=5)
        cal_end_date.grid(row=0, column=3, padx=5, pady=5)
        btn_ok.grid(row=1, columnspan=4, padx=5, pady=5)
        def on_closing():
            self.progress_bar.start()
            sd = cal_start_date.get_date().strftime('%Y-%m-%d %H-%M-%S')
            ed = cal_end_date.get_date().strftime('%Y-%m-%d %H-%M-%S')
            dr_files = self.archive.date_range(sd, ed)
            self.refresh_daterange_plots(dr_files)
            self.progress_bar.stop()
            top.destroy()
    
    def clear_plots(self):
        self.thp_figure.th.cla()
        self.thp_figure.th2.cla()
        self.thp_figure.p.cla()
        self.pms_figure.pms_concentration.cla()
        self.pms_figure.pms_counts.cla()
    
    def refresh_plots(self, timespan: str):
        resample_dict = {'1h': '5T', '8h': '20T', '24h': 'H',
                         '7d': 'H', '1m': 'D', '6m': 'D',
                         '1y': 'W'}
        data_files = os.listdir(self.archive.data_dir)
        fn_delta = self.archive.cap_archive_list(data_files, limit=timespan)
        self.plot_data = self.archive.create_df(fn_delta)
        # Clear plots
        self.clear_plots()
        # Plot temperature, humidity, pressure
        temp_min = 18
        temp_max = 24
        self.thp_figure.th.plot(self.plot_data.index, self.plot_data['temperature'], color='C0', label='temperature')
        self.thp_figure.th.axhline(y=temp_min, color='C0', linestyle='--', label='lower temp limit')
        self.thp_figure.th.axhline(y=temp_max, color='C0', linestyle='--', label='upper temp limit')
        self.thp_figure.th.fill_between(self.plot_data.index, temp_min, temp_max, color='C0', alpha=0.2)
        self.thp_figure.th2.plot(self.plot_data.index, self.plot_data['humidity'], color='C1', label='humidity')
        self.thp_figure.th2.axhline(y=40, color='C1', linestyle='--', label='lower humidity limit')
        self.thp_figure.th2.axhline(y=70, color='C1', linestyle='--', label='upper humidity limit')
        self.thp_figure.th2.fill_between(self.plot_data.index, 40, 70, color='C1', alpha=0.2)
        self.thp_figure.p.plot(self.plot_data.index, self.plot_data['pressure'], color='C2', label='pressure')
        # Plot particle data
        self.plot_data_rs = self.plot_data.resample(resample_dict[timespan]).mean()
        self.pms_figure.pms_concentration.plot(self.plot_data_rs.index, self.plot_data_rs['pm10_standard'], label='1.0 $\mu$m')
        self.pms_figure.pms_concentration.plot(self.plot_data_rs.index, self.plot_data_rs['pm25_standard'], label='2.5 $\mu$m')
        self.pms_figure.pms_concentration.plot(self.plot_data_rs.index, self.plot_data_rs['pm100_standard'], label='10.0 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data_rs.index, self.plot_data_rs['particles_03um'], label='0.3 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data_rs.index, self.plot_data_rs['particles_05um'], label='0.5 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data_rs.index, self.plot_data_rs['particles_10um'], label='1.0 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data_rs.index, self.plot_data_rs['particles_25um'], label='2.5 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data_rs.index, self.plot_data_rs['particles_50um'], label='5.0 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data_rs.index, self.plot_data_rs['particles_100um'], label='10.0 $\mu$m')
        self.reset_figures()

    def refresh_daterange_plots(self, daterange_files: list):
        self.plot_data = self.archive.create_df(daterange_files)
        # Clear plots
        self.clear_plots()
        # Plot temperature, humidity, pressure
        temp_min = 18
        temp_max = 24
        self.thp_figure.th.plot(self.plot_data.index, self.plot_data['temperature'], color='C0', label='temperature')
        self.thp_figure.th.axhline(y=temp_min, color='C0', linestyle='--', label='lower temp limit')
        self.thp_figure.th.axhline(y=temp_max, color='C0', linestyle='--', label='upper temp limit')
        self.thp_figure.th.fill_between(self.plot_data.index, temp_min, temp_max, color='C0', alpha=0.2)
        self.thp_figure.th2.plot(self.plot_data.index, self.plot_data['humidity'], color='C1', label='humidity')
        self.thp_figure.th2.axhline(y=40, color='C1', linestyle='--', label='lower humidity limit')
        self.thp_figure.th2.axhline(y=70, color='C1', linestyle='--', label='upper humidity limit')
        self.thp_figure.th2.fill_between(self.plot_data.index, 40, 70, color='C1', alpha=0.2)
        self.thp_figure.p.plot(self.plot_data.index, self.plot_data['pressure'], color='C2', label='pressure')
        # Plot particle data
        # self.plot_data_rs = self.plot_data.resample(resample_dict[daterange_files]).mean()
        self.pms_figure.pms_concentration.plot(self.plot_data.index, self.plot_data['pm10_standard'], label='1.0 $\mu$m')
        self.pms_figure.pms_concentration.plot(self.plot_data.index, self.plot_data['pm25_standard'], label='2.5 $\mu$m')
        self.pms_figure.pms_concentration.plot(self.plot_data.index, self.plot_data['pm100_standard'], label='10.0 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data.index, self.plot_data['particles_03um'], label='0.3 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data.index, self.plot_data['particles_05um'], label='0.5 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data.index, self.plot_data['particles_10um'], label='1.0 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data.index, self.plot_data['particles_25um'], label='2.5 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data.index, self.plot_data['particles_50um'], label='5.0 $\mu$m')
        self.pms_figure.pms_counts.plot(self.plot_data.index, self.plot_data['particles_100um'], label='10.0 $\mu$m')
        self.reset_figures()

    def reset_figures(self):
        # Reset figures
        self.thp_figure.reset_thp()
        self.pms_figure.reset_pms()
        # align temperature and humidity y ticks
        t_lim = self.thp_figure.th.get_ylim()
        h_lim = self.thp_figure.th2.get_ylim()
        lim_func = lambda x: h_lim[0] + (x - t_lim[0]) / (t_lim[1] - t_lim[0]) * (h_lim[1] - h_lim[0])
        ticks = lim_func(self.thp_figure.th.get_yticks())
        self.thp_figure.th2.yaxis.set_major_locator(FixedLocator(ticks))
        # re-draw plots
        self.thp_figure.thp_plot.draw()
        self.pms_figure.pms_plot.draw()
    
    def realtime(self):
        buffer = []
        if self.sensor_active:
            rta = True
            while rta:
                num_buffer = self.sensor_daemon.sampling_buffer.qsize()
                for i in range(num_buffer):
                    buffer.append(ReadArchive.txt2num(self.sensor_daemon.sampling_buffer.get()))
                self.clear_plots()
                dt = [datetime.fromtimestamp(i[0]) for i in buffer]
                self.thp_figure.th.plot(dt, [j[1] for j in buffer], color='C0', label='temperature')
                self.thp_figure.th2.plot(dt, [j[2] for j in buffer], color='C1', label='humidity')
                self.thp_figure.p.plot(dt, [j[3] for j in buffer], color='C2', label='pressure')
                self.pms_figure.pms_concentration.plot(dt, [j[4] for j in buffer], label='1.0 $\mu$m')
                self.pms_figure.pms_concentration.plot(dt, [j[5] for j in buffer], label='2.5 $\mu$m')
                self.pms_figure.pms_concentration.plot(dt, [j[6] for j in buffer], label='10.0 $\mu$m')
                self.pms_figure.pms_counts.plot(dt, [j[7] for j in buffer], label='0.3 $\mu$m')
                self.pms_figure.pms_counts.plot(dt, [j[8] for j in buffer], label='0.5 $\mu$m')
                self.pms_figure.pms_counts.plot(dt, [j[9] for j in buffer], label='1.0 $\mu$m')
                self.pms_figure.pms_counts.plot(dt, [j[10] for j in buffer], label='2.5 $\mu$m')
                self.pms_figure.pms_counts.plot(dt, [j[11] for j in buffer], label='5.0 $\mu$m')
                self.pms_figure.pms_counts.plot(dt, [j[12] for j in buffer], label='10.0 $\mu$m')
                self.reset_figures()
                sleep(self.sensor_daemon.sampling_interval)
                if self.realtime_active.qsize() > 0:
                    self.realtime_active.get()
                    rta = False
        else:
            pass
    
    def start_realtime_process(self):
        if self.sensor_active:
            self.realtime_process = Process(target=self.realtime)
            self.realtime_process.start()
    
    def stop_realtime_process(self):
        self.realtime_process.terminate()

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
        # self.fig.autofmt_xdate()
        self.thp_plot = FigureCanvasTkAgg(self.fig, master=self)
        self.th2 = self.th.twinx()
        # Configure subplots
        self.th.set_title('Temperature | Humidity')
        self.th.set_ylabel('Temperature [$^\circ$C]', color='C0')
        self.p.set_xlabel('Date', loc='left')
        self.th2.set_ylabel('Humidity [%RH]', color='C1')
        self.th2.yaxis.set_label_position('right')
        self.th.grid()
        self.p.set_title('Pressure')
        self.p.set_ylabel('Pressure [mBar]', color='C2')
        self.p.grid()
        t_lim = self.th.get_ylim()
        h_lim = self.th2.get_ylim()
        lim_func = lambda x: h_lim[0] + (x - t_lim[0]) / (t_lim[1] - t_lim[0]) * (h_lim[1] - h_lim[0])
        ticks = lim_func(self.th.get_yticks())
        self.th2.yaxis.set_major_locator(FixedLocator(ticks))
        self.thp_plot.draw()
    
    def reset_thp(self):
        self.th.set_title('Temperature | Humidity')
        self.th.set_ylabel('Temperature [$^\circ$C]', color='C0')
        self.p.set_xlabel('Date', loc='left')
        # rotate x tick labels by 45 degrees
        for tick in self.p.get_xticklabels():
            tick.set_rotation(30)
        self.th2.set_ylabel('Humidity [%RH]', color='C1')
        self.th2.yaxis.set_label_position('right')
        self.th2.yaxis.tick_right()
        self.th.grid()
        self.p.set_title('Pressure')
        self.p.set_ylabel('Pressure [mBar]', color='C2')
        self.p.grid()
    
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
        self.fig, (self.pms_concentration, self.pms_counts) = plt.subplots(nrows=2, ncols=1,
            figsize=(1280 / self.screen_dpi, 500 / self.screen_dpi),
            dpi=self.screen_dpi)
        self.fig.subplots_adjust(hspace=0.5)
        self.pms_plot = FigureCanvasTkAgg(self.fig, master=self)
        # self.pms_concentration.bar(concentration.keys(), concentration.values())
        # self.pms_counts.bar(counts.keys(), counts.values())
        self.pms_concentration.plot([1,2,3,4], [2,3,4,5])
        self.pms_counts.scatter([1,2,3,4], [2,3,4,5])
        self.pms_concentration.set_title('Particle Concentration')
        self.pms_concentration.set_ylabel('$\mu$g/m$^3$')
        self.pms_concentration.set_xlabel('Particle Size [$\mu$m]')
        self.pms_counts.set_title('Particle Counts')
        self.pms_counts.set_yscale('log')
        self.pms_counts.set_ylabel('Quantity per dL Air')
        self.pms_counts.set_xlabel('Particle Size [$\mu$m]')
        self.fig.subplots_adjust(bottom=0.1, top=0.95)
        self.pms_plot.draw()
    
    def reset_pms(self):
        # Reset concentration figure
        self.pms_concentration.set_title('Particle Concentration')
        self.pms_counts.set_title('Particle Counts')
        self.pms_concentration.set_ylabel('$\mu$g/m$^3$')
        self.pms_concentration.set_xlabel('Date', loc='left')
        self.pms_concentration.grid()
        self.pms_concentration.legend()
        # Reset counts figure
        self.pms_counts.set_title('Particle Counts')
        self.pms_counts.set_yscale('log')
        self.pms_counts.set_ylabel('Quantity per dL Air')
        self.pms_counts.set_xlabel('Date', loc='left')
        self.pms_counts.grid()
        # self.pms_counts.legend()
        # pos = self.pms_counts.get_position()
        pos = Bbox([[0.125, 0.1], [0.9, 0.44]])
        self.pms_counts.set_position([pos.x0, pos.y0, pos.width * 0.95, pos.height])
        self.pms_counts.legend(loc='center right', bbox_to_anchor=(1.125, 0.5))
        # rotate x tick labels by 45 degrees
        for tick in self.pms_concentration.get_xticklabels():
            tick.set_rotation(30)
        for tick in self.pms_counts.get_xticklabels():
            tick.set_rotation(30)