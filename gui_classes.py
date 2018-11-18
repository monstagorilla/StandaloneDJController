from scipy.io import wavfile
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color
from numpy import mean
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
    def __init__(self, title, bpm, path, wav_data):
        self.title = title
        self.bpm = bpm
        self.path = path
        self.wav_data = wav_data


class AudioVisualizer(Widget):
    wav_data = ListProperty([])

    def __init__(self, **kwargs):
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

    def _update_pos(self, instance, value):
        self.abs_pos = instance.pos
        self.on_wav_data(None, None)

    def _update_size(self, instance, value):
        self.abs_size = instance.size
        self.on_wav_data(None, None)

    def update_track_pos(self):
        index_pos = int(self.abs_size[0] * self.track_pos * 4)
        self.line0.points = self.line_points[:index_pos]
        self.line1.points = self.line_points[index_pos:]

    def on_wav_data(self, instance, value):  # TODO realy need instance, value?
        if self.width > 0:
            chunk_size = int(len(self.wav_data) / self.width)
        else:
            logger.warning("width = 0")
            return
        mean_data = []
        for x in range(0, int(self.width)):
            try:
                mean_data.append(mean(self.wav_data[x * chunk_size: (x + 3) * chunk_size]))
            except Exception as e:
                logger.error(e)

        scaling_factor = self.height/max(mean_data)/1.5
        self.line_points = []
        for x in range(0, int(self.width)):
            self.line_points.extend([self.abs_pos[0] + x, self.abs_pos[1] - mean_data[x] * scaling_factor + self.abs_size[1] / 2,
                                     self.abs_pos[0] + x, self.abs_pos[1] + mean_data[x] * scaling_factor + self.abs_size[1] / 2])
        self.update_track_pos()


class LabelWithBackground(Label):
    color_widget = ListProperty([0/256, 38/256, 53/256])

    def __init__(self, **kwargs):
        super(LabelWithBackground, self).__init__(**kwargs)
