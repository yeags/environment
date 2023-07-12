from time import timedelta
from datetime import datetime
import pandas as pd
import re
from tkinter import ttk
import numpy as np

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

    def create_df(self, files: list, progress_object: ttk.Progressbar) -> pd.DataFrame:
        for i, file in enumerate(files):
            if '.txt' not in file:
                files.pop(i)
        progress_object.configure(maximum=len(files))
        with open(self.data_dir + files[0]) as f:
            header = f.readline()
            header = header[:-1].split(' ')
        data = []
        for file in files:
            with open(self.data_dir + file) as f:
                f.readline()
                contents = f.read()
            lines = contents[:-1].split('\n')
            for line in lines:
                data.append(self.txt2num(line[:-1]))
            progress_object.step()
            progress_object.update()
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
        return df

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