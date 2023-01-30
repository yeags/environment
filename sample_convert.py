import pandas as pd
import matplotlib.pyplot as plt
import os, sys
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
from multiprocessing import Pool, Queue
np.set_printoptions(suppress=True)

def txt2num(sample: str):
    sample = sample[:-1].split(' ')
    nums = []
    for value in sample:
        try:
            nums.append(float(value))
        except ValueError:
            nums.append(np.nan)
    return nums

# def create_df(filename: str) -> pd.DataFrame:
#     with open(filename) as file:
#         header = file.readline()
#         data = file.read()
    
#     header = header[:-1].split(' ')
#     data_lines = data[:-1].split('\n')
#     data_array = []
#     for line in data_lines:
#         data_array.append(txt2num(line))
#     data_array = np.array(data_array)
#     df = pd.DataFrame(data=data_array, columns=header)
#     df_datetime = pd.to_datetime([dt.fromtimestamp(i) for i in df['timestamp'].values])
#     df['datetime'] = df_datetime
#     df = df.set_index('datetime')
#     df = df.drop(columns=['timestamp'])
#     return df

# def concat_df(files):
#     df = create_df(files[0])
#     for file in files[1:]:
#         df_file = create_df(file)
#         df = pd.concat([df, df_file])
#     return df

def create_df(files: list) -> pd.DataFrame:
    for i, file in enumerate(files):
        if '.txt' not in file:
            files.pop(i)
    with open(files[0]) as f:
        header = f.readline()
        header = header[:-1].split(' ')
    data = []
    for file in files:
        with open(file) as f:
            f.readline()
            contents = f.read()
        lines = contents[:-1].split('\n')
        for line in lines:
            data.append(txt2num(line))
    df = pd.DataFrame(data=data, columns=header)
    df_datetime = pd.to_datetime([dt.fromtimestamp(i) for i in df['timestamp'].values])
    df['datetime'] = df_datetime
    df = df.set_index('datetime')
    df = df.drop(columns=['timestamp'])
    return df

if __name__ == '__main__':
    data_dir = './data/'
    files = os.listdir('./data')
    for i, name in enumerate(files):
        files[i] = data_dir + name
    for i , name in enumerate(files):
        if '.txt' not in name:
            files.pop(i)

    df = create_df(files)
    print(f'df size: {round(sys.getsizeof(df)/1024**2, 2)} MB')
    # print(df.resample('2W').mean())
    print(df[df.index > dt.now() - timedelta(days=60)].resample('D').mean())