import tkinter as tk
from tkinter import ttk
from time import sleep

class ProgressApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # self.geometry('640x480')
        self.title('Progress bar tester')
        self.archive = ReadArchive()
        self.create_widgets()
        self.mainloop()
    
    def create_widgets(self):
        self.pb = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.btn_read = ttk.Button(self, text='Read Files', command=lambda: self.archive.read_files(self.pb))
        self.btn_exit = ttk.Button(self, text='Exit', command=self.destroy)
        self.pb.grid(column=0, row=0, columnspan=2, sticky='ew')
        self.btn_read.grid(column=0, row=1, sticky='e')
        self.btn_exit.grid(column=1, row=1, sticky='w')
    
class ReadArchive:
    def __init__(self):
        pass
    def read_files(self, step_object: ttk.Progressbar):
        files = [i for i in range(200)]
        step_object.configure(maximum=len(files))
        for file in files:
            print(file, step_object['value'])
            step_object.step()
            step_object.update()
            sleep(0.01)

if __name__ == '__main__':
    test = ProgressApp()