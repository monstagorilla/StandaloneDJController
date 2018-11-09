from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from scipy.io import wavfile
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color
from numpy import mean
from typing import List
from player import Player


class Track:
    def __init__(self, title: str, bpm: str, path: str, wav_data: List[int]) -> None:
        self.title = title
        self.bpm = bpm
        self.path = path
        self.wav_data = wav_data


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

    def _update_pos(self, instance, value) -> None:
        print("type: {}".format(instance))
        self.abs_pos = instance.pos
        self.on_wav_data(instance, value)

    def _update_size(self, instance, value) -> None:
        self.abs_size = instance.size
        self.on_wav_data(instance, value)

    def update_track_pos(self) -> None:
        index_pos = int(self.abs_size[0] * self.track_pos * 4)
        self.line0.points = self.line_points[:index_pos]
        self.line1.points = self.line_points[index_pos:]

    def on_wav_data(self, instance, value) -> None:
        if self.width > 0:
            chunk_size = int(len(self.wav_data) / self.width)
        else:
            print("in on_wav_data: width = 0")
            return
        mean_data = []
        for x in range(0, int(self.width)):
            try:
                mean_data.append(mean(self.wav_data[x * chunk_size: (x + 3) * chunk_size]))
            except Exception as Argument:
                print("Error in on_wav_data: " + str(Argument))

        scaling_factor = self.height/max(mean_data)/1.5
        self.line_points = []
        for x in range(0, int(self.width)):
            self.line_points.extend([self.abs_pos[0] + x, self.abs_pos[1] - mean_data[x] * scaling_factor + self.abs_size[1] / 2,
                                     self.abs_pos[0] + x, self.abs_pos[1] + mean_data[x] * scaling_factor + self.abs_size[1] / 2])
        self.update_track_pos()


class LabelWithBackground(Label):
    color_widget = ListProperty([0/256, 38/256, 53/256])

    def __init__(self, **kwargs) -> None:
        super(LabelWithBackground, self).__init__(**kwargs)


class GUI(BoxLayout):
    def __init__(self, **kwargs) -> None:
        super(GUI, self).__init__(**kwargs)
        self.ids.av_l.bind(size=self.ids.av_l._update_size, pos=self.ids.av_l._update_pos)
        self.ids.av_r.bind(size=self.ids.av_r._update_size, pos=self.ids.av_r._update_pos)
        self.ids.av_l.color_deck0.rgb = self.color_deck_l0
        self.ids.av_l.color_deck1.rgb = self.color_deck_l1
        self.ids.av_r.color_deck0.rgb = self.color_deck_r0
        self.ids.av_r.color_deck1.rgb = self.color_deck_r1

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.player = Player(self)


    #----------------------------------Properties------------------------------------#
    # GUI globals
    is_browsing = ObjectProperty(0)  # 0 => no browser, 1 => browser on deck 1, 2 => browser on deck 2
    color_background = ListProperty([1/256, 52/256, 64/256])
    color_deck_l0 = ListProperty([171 / 256, 26 / 256, 37 / 256])
    color_deck_l1 = ListProperty([80 / 256, 10 / 256, 15 / 256])
    color_deck_r0 = ListProperty([217/256, 121/256, 37/256])
    color_deck_r1 = ListProperty([100/256, 60/256, 15/256])
    color_font = ListProperty([239/256, 231/256, 190/256])

    # Track Infos
    title0 = StringProperty("left")
    title1 = StringProperty("right")
    bpm0 = StringProperty("128")
    bpm1 = StringProperty("70")
    path0 = StringProperty("path0")  # necessary?
    path1 = StringProperty("path1")


    # Current State
    time0 = StringProperty("1:45/3:05")
    time1 = StringProperty("17:04/32:00")
    position0 = NumericProperty(0.2)
    position1 = NumericProperty(0.9)
    pitch0 = StringProperty("0")
    pitch1 = StringProperty("+0.1")
    is_playing0 = BooleanProperty(True)
    is_playing1 = BooleanProperty(False)
    is_on_headphone0 = BooleanProperty(True)
    is_on_headphone1 = BooleanProperty(False)

    def update_gui(self, track0: Track = None, track1: Track = None, position0: float = None, position1: float = None,
                   time0: str = None, time1: str = None, pitch0: str = None, pitch1: str = None,
                   is_playing0: bool = None, is_playing1: bool = None, is_on_headphone0: bool = None,
                   is_on_headphone1: bool = None) -> None:
        if track0 is not None:
            self.title0 = track0.title
            self.bpm0 = track0.bpm
            self.path0 = track0.path
            self.ids.av_l.wav_data = track0.wav_data
        if track1 is not None:
            self.title0 = track0.title
            self.bpm0 = track0.bpm
            self.path0 = track0.path
            self.ids.av_l.wav_data = track0.wav_data
        if position0 is not None:
            self.position0 = position0
        if position1 is not None:
            self.position1 = position1
        if time0 is not None:
            self.time0 = time0
        if time1 is not None:
            self.time1 = time1
        if pitch0 is not None:
            self.pitch0 = pitch0
        if pitch1 is not None:
            self.pitch1 = pitch1
        if is_playing0 is not None:
            self.is_playing0 = is_playing0
        if is_playing1 is not None:
            self.is_playing1 = is_playing1
        if is_on_headphone0 is not None:
            self.is_on_headphone0 = is_on_headphone0
        if is_on_headphone1 is not None:
            self.is_on_headphone1 = is_on_headphone1

    def _keyboard_closed(self) -> None:
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers) -> bool:
        if keycode[1] == 'l':
            raw_data = wavfile.read('/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav')[1]
            new_wav_data = []
            for x in raw_data[::50]:
                new_wav_data.append(abs(x[0]))
            self.ids.av_l.wav_data = new_wav_data
        elif keycode[1] == 'r':
            raw_data = wavfile.read('/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav')[1]
            new_wav_data = []
            for x in raw_data[::50]:
                new_wav_data.append(abs(x[0]))
            self.ids.av_r.wav_data = new_wav_data
        elif keycode[1] == "q":
            raw_data = wavfile.read('/home/monstagorilla/Music/temp/Super Trouper - Mamma Mia.wav')[1]
            new_wav_data = []
            for x in raw_data[::50]:
                new_wav_data.append(abs(x[0]))
            self.update_gui(track0=Track("scuuuuurrrr", "200", "pathlol", new_wav_data))
        elif keycode[1] == "1":
            self.position0 = 0.1
        elif keycode[1] == "2":
            self.position0 = 0.2
        elif keycode[1] == "3":
            self.position0 = 0.3
        elif keycode[1] == "4":
            self.position0 = 0.4
        elif keycode[1] == "5":
            self.position0 = 0.5
        elif keycode[1] == "6":
            self.position0 = 0.6
        elif keycode[1] == "7":
            self.position0 = 0.7
        elif keycode[1] == "8":
            self.position0 = 0.8
        elif keycode[1] == "9":
            self.position0 = 0.9
        return True

    def on_position0(self, instance, value) -> None:
        self.ids.av_l.track_pos = value
        self.ids.av_l.update_track_pos()

    def on_position1(self, instance, value) -> None:
        self.ids.av_r.track_pos = value
        self.ids.av_r.update_track_pos()


class GUIApp(App):
    def build(self) -> GUI:
        return GUI()

