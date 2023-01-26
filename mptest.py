from multiprocessing import Process, Queue
from time import sleep

class LoopDaemon:
    def __init__(self):
        self.loop_counter = 0
        self.reset_threshold = 10
        self.sampling_delay = 1
        self.q = Queue()
        self.daemon = Process(target=self.start_loop)
        self.daemon.start()
        print(f'daemon pid: {self.daemon.pid}')
    
    def start_loop(self):
        try:
            while True:
                while self.loop_counter < self.reset_threshold:
                    self.q.put(self.loop_counter)
                    sleep(self.sampling_delay)
                    self.loop_counter += 1
                self.loop_counter = 0
        except KeyboardInterrupt:
            exit()

if __name__ == '__main__':
    d = LoopDaemon()
    sleep(6)
    max_buffer = 5
    try:
        if d.q.qsize() >= max_buffer:
            for i in range(max_buffer):
                d.q.get()
        while True:
            if d.q.empty() == False:
                print(f'queue buffer: {d.q.qsize()}')
                print(f'queue value: {d.q.get()}')
    except KeyboardInterrupt:
        exit()