from time import sleep,time

class Await:
    def __init__(self):
        self.init()

    def init(self):
        self.t = time()

    def wait(self, sec):
        self.t = self.t + sec
        sleep_time = self.t - time()
        if sleep_time > 0:
            sleep(sleep_time)
        return sleep_time