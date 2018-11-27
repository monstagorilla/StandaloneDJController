# CLEAN

from kivy.properties import ListProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color
import logging
import sys

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class Track:
    def __init__(self, title="", bpm="0 bpm", path=""):
        self.title = title
        self.bpm = bpm
        self.path = path


class AudioVisualizer(Widget):
    wav_data = ListProperty([])

    def __init__(self, **kwargs) -> None:
        super(AudioVisualizer, self).__init__(**kwargs)
        self.abs_pos = [0, 0]
        self.abs_size = [0, 0]
        self.line_points = []
        self.track_pos = 0
        with self.canvas:
            self.color_deck0 = Color()
            self.line0 = Line(width=1)
            self.color_deck1 = Color()
            self.line1 = Line(width=1)

    def update_pos(self, instance, value) -> None:
        self.abs_pos = instance.pos
        self.on_wav_data(None, None)

    def update_size(self, instance, value) -> None:
        self.abs_size = instance.size
        self.on_wav_data(None, None)

    def update_track_pos(self) -> None:
        index_pos = int(self.abs_size[0] * self.track_pos) * 4  # multiply by 4 because of chunks(len=4) in line_points
        self.line0.points = self.line_points[:index_pos]
        self.line1.points = self.line_points[index_pos:]

    def on_wav_data(self, instance, value) -> None:
        if not self.wav_data:
            logger.error("no wav_data")
            return
        if max(self.wav_data) == 0:
            logger.error("cannot divide by max_value = 0")
            return
        scaling_factor = self.height/max(self.wav_data) / 1.5  # 1.5 is a hardcoded factor
        self.line_points = []
        for x in range(0, int(self.width)):
            self.line_points.extend([self.abs_pos[0] + x, self.abs_pos[1] - self.wav_data[x] * scaling_factor + self.abs_size[1] / 2,
                                     self.abs_pos[0] + x, self.abs_pos[1] + self.wav_data[x] * scaling_factor + self.abs_size[1] / 2])
        self.update_track_pos()  # TODO maybe not necessary


class LabelWithBackground(Label):
    color = [0/256, 38/256, 53/256]
    color_widget = ListProperty(color)

    def __init__(self, **kwargs):
        super(LabelWithBackground, self).__init__(**kwargs)
