from player import Player
from trackloader import TrackLoader
import logging
from kivy.app import App
from kivy.uix.button import Button
import sys

import shutil
import os


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
        self.test_trackloader()

    def test_trackloader(self):
        t = TrackLoader(self.p, "/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav", 0, self.clear_temp_dir)
        t.start()

    def clear_temp_dir(self):
        logger.info("clearing temp")


class MyApp(App):
    def build(self):
        return TestKivy()


if __name__ == '__main__':
    a = MyApp()
    a.run()