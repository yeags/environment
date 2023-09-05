from datetime import datetime, timedelta
import pandas as pd
import re, os
from tkinter import ttk
import numpy as np
from concurrent.futures import ProcessPoolExecutor

class ReadArchive:
    def __init__(self, data_dir='./data/'):
        self.data_dir = data_dir
        self.fn_format = '%Y-%m-%d %H-%M-%S'
        self.re_compile = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}')
        self.delta_dict = {'1h': timedelta(hours=1), '8h': timedelta(hours=8), '24h': timedelta(hours=24),
                           '7d': timedelta(days=7), '1m': timedelta(days=30), '6m': timedelta(days=90),
                           '1y': timedelta(days=365)}
    
    def txt2num(self, sample: str) -> list:
        sample = sample.split(' ')
        nums = []
        for value in sample:
            try:
                nums.append(float(value))
            except ValueError:
                nums.append(np.nan)
        return nums
    
    def date_range(self, start_date: str, end_date: str) -> list:
        start_date = datetime.strptime(start_date, self.fn_format)
        end_date = datetime.strptime(end_date, self.fn_format)
        all_files = os.listdir(self.data_dir)
        selected_files = []
        for file in all_files:
            match = self.re_compile.search(file)
            if match:
                file_date = datetime.strptime(match.group(), self.fn_format)
                if start_date <= file_date <= end_date:
                    selected_files.append(file)
        return selected_files

    def create_df(self, files: list) -> pd.DataFrame:
        for i, file in enumerate(files):
            if '.txt' not in file:
                files.pop(i)
        with open(self.data_dir + files[0]) as f:
            header = f.readline()
            header = header[:-1].split(' ')
        with ProcessPoolExecutor() as executor:
            data = [sample for result in executor.map(self.read_file, files) for sample in result]
        data = self.remove_nan(data)
        df = pd.DataFrame(data=data, columns=header)
        df_datetime = pd.to_datetime([datetime.fromtimestamp(i) for i in df['timestamp'].values])
        df['datetime'] = df_datetime
        df = df.set_index('datetime')
        df = df.drop(columns=['timestamp'])
        df = df.dropna()
        df['particles_03um'] = df['particles_03um'] - df['particles_05um']
        df['particles_05um'] = df['particles_05um'] - df['particles_10um']
        df['particles_10um'] = df['particles_10um'] - df['particles_25um']
        df['particles_25um'] = df['particles_25um'] - df['particles_50um']
        df['particles_50um'] = df['particles_50um'] - df['particles_100um']
        df = df.sort_index()
        return df

    def remove_nan(self, data: list) -> list:
        pop_list = []
        for i, sample in enumerate(data):
            if np.isnan(sample[0]):
                pop_list.append(i)
        for i in pop_list[::-1]:
            data.pop(i)
        return data

    def read_file(self, filename):
        with open(self.data_dir + filename) as f:
            f.readline()
            contents = f.read()
        lines = contents[:-1].split('\n')
        data = []
        for line in lines:
            if line.endswith(' '):
                data.append(self.txt2num(line[:-1]))
            else:
                data.append(self.txt2num(line))
        return data

    def cap_archive_list(self, files: list, limit='1h') -> list:
        files_str = ' '.join(files)
        fn_list = re.findall(self.re_compile, files_str)
        fn_datetime = []
        filenames = []
        for fn in fn_list:
            fn_datetime.append(datetime.strptime(fn, self.fn_format))
        recent_datetime = max(fn_datetime)
        for time in fn_datetime:
            if time >= recent_datetime - self.delta_dict[limit]:
                filenames.append(time.strftime(self.fn_format) + '.txt')
        return filenames

if __name__ == '__main__':
    pass