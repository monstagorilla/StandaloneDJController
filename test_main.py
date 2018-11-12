from player import Player
import logging
from kivy.app import App
from kivy.uix.button import Button
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class TestKivy(Button):
    def __init__(self):
        super(TestKivy, self).__init__()
        self.p = Player()
        self.p.start()
        self.p.table[0].setSound(path="/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav")
        self.p.pointer[0].table = self.p.table[0]
        self.p.phasor[0].reset()
        self.p.phasor[0].freq = 0
        self.p.start_stop(0)


class MyApp(App):
    def build(self):
        return TestKivy()


if __name__ == '__main__':
    a = MyApp()
    a.run()