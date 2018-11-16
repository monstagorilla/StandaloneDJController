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
from file_browser import FileBrowser
from decoder import Decoder
from kivy.clock import Clock
import logging
from trackloader import TrackLoader
import sys
from pyo import *
from multiprocessing import Pipe

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


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
        self.abs_pos = instance.pos
        self.on_wav_data()

    def _update_size(self, instance, value) -> None:
        self.abs_size = instance.size
        self.on_wav_data()

    def update_track_pos(self) -> None:
        index_pos = int(self.abs_size[0] * self.track_pos * 4)  # multiply by 4 because of chunks(len=4) in line_points
        self.line0.points = self.line_points[:index_pos]  # TODO maybe not pixel perfect
        self.line1.points = self.line_points[index_pos:]

    def on_wav_data(self) -> None:  # TODO problem with missing instance/value parameter?
        if self.width > 0:
            chunk_size = int(len(self.wav_data) / self.width)
        else:
            logger.warning("width = 0 -> cannot divide")
            return
        mean_data = []
        for x in range(0, int(self.width)):
            try:
                mean_data.append(mean(self.wav_data[x * chunk_size: (x + 3) * chunk_size]))
            except Exception as e:
                logger.warning(e)

        scaling_factor = self.height/max(mean_data)/1.5  # 1.5 is a hardcoded factor
        self.line_points = []
        for x in range(0, int(self.width)):
            self.line_points.extend([self.abs_pos[0] + x, self.abs_pos[1] - mean_data[x] * scaling_factor + self.abs_size[1] / 2,
                                     self.abs_pos[0] + x, self.abs_pos[1] + mean_data[x] * scaling_factor + self.abs_size[1] / 2])
        self.update_track_pos()  # TODO maybe not necessary


class LabelWithBackground(Label):
    color_widget = ListProperty([0/256, 38/256, 53/256])

    def __init__(self, **kwargs) -> None:  # TODO not needed?
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

        self.rx_player, tx_player = Pipe(duplex=False)
        self.rx_track_loader, self.tx_track_loader = Pipe(duplex=False)

        self.player = Player(tx_player)
        #self.player.start()

        self.file_browser = FileBrowser()

        self.cur_browser = 0
        self.temp_widget_tree = [None, None]
        self.is_browsing = [False, False]

        Clock.schedule_interval(self.decoder.update_decoder, 0.1)  # TODO choose good interval time
        Clock.schedule_interval(self.handler_player, 0.1)  # TODO choose good interval time



    #----------------------------------Properties------------------------------------#
    # GUI globals
    is_browsing = ObjectProperty(0)  # 0 => no browser, 1 => browser on deck 1, 2 => browser on deck 2
    color_background = ListProperty([1/256, 52/256, 64/256])
    color_deck_l0 = ListProperty([171 / 256, 26 / 256, 37 / 256])
    color_deck_l1 = ListProperty([80 / 256, 10 / 256, 15 / 256])
    color_deck_r0 = ListProperty([217/256, 121/256, 37/256])
    color_deck_r1 = ListProperty([100/256, 60/256, 15/256])
    color_font = ListProperty([239/256, 231/256, 190/256])

    # TODO correct default values
    # Track Info
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

    def handler_player(self, dt):
        if self.rx_player.poll():
            d = self.rx_player.recv()
            self.update_gui(position0=d[0], position1=d[1], time0=d[2], time1=d[3], pitch0=d[4], pitch1=d[5],
                            is_playing0=d[6], is_playing1=d[7], is_on_headphone0=d[8], is_on_headphone1=d[9])

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
        if keycode[1] == "b":
            if self.is_browsing[0]:
                self.stop_browsing(0)
            else:
                self.start_browsing(0)
        if keycode[1] == "n":
            if self.is_browsing[1]:
                self.stop_browsing(1)
            else:
                self.start_browsing(1)

        elif self.is_browsing[self.cur_browser]:
            if keycode[1] == 'down':
                count = len(self.file_browser._items)
                has_selected = False
                for i in range(0, count):
                    if self.file_browser._items[i].is_selected:
                        has_selected = True
                        if i < count - 1:
                            self.file_browser._items[i].is_selected = False
                            self.file_browser._items[i + 1].is_selected = True
                            self.file_browser.layout.ids.scrollview.scroll_to(self.file_browser._items[i + 1])
                        break
                if not has_selected:
                    self.file_browser._items[0].is_selected = True
            elif keycode[1] == 'up':
                count = len(self.file_browser._items)
                has_selected = False
                for i in range(0, count):
                    if self.file_browser._items[i].is_selected:
                        has_selected = True
                        if i > 0:
                            self.file_browser._items[i].is_selected = False
                            self.file_browser._items[i - 1].is_selected = True
                            self.file_browser.layout.ids.scrollview.scroll_to(self.file_browser._items[i - 1])
                        break
                if not has_selected:
                    self.file_browser._items[count - 1].is_selected = True

            elif keycode[1] == 'right':
                for x in self.file_browser._items:
                    if x.is_selected:
                        if self.file_browser.file_system.is_dir(x.path):
                            self.file_browser.path = x.path
                        else:
                            logger.info("load_track")
                            track_name = "/".join(x.path.split("/")[-1:])
                            if self.file_browser.get_codec(x.path) == "mp3" and not self.decoder.decode_is_running:
                                new_track = [x.path, self.cur_browser, "mp3"]
                                self.decoder.load_mp3(track_name, new_track)
                                logger.info("new track: " + str(new_track))
                            #elif self.file_browser.get_codec(self.path + "/" + track_name) == "wav":
                                #pass
                            #    t = TrackLoader(self.player, self.path + "/" + track_name, self.cur_browser, self.clear_temp_dir)
                            #    t.start()
                                #self.player.snd_view = True

            elif keycode[1] == 'left':
                if self.file_browser.path != self.file_browser.rootpath:
                    self.file_browser.path = "/".join(self.file_browser.path.split("/")[:-1])

        return True

    def on_position0(self, instance, value) -> None:
        self.ids.av_l.track_pos = value
        self.ids.av_l.update_track_pos()

    def on_position1(self, instance, value) -> None:
        self.ids.av_r.track_pos = value
        self.ids.av_r.update_track_pos()

    def start_browsing(self, channel: int) -> None:
        if self.is_browsing[channel]:
            logger.info("already browsing.")
            return
        # TODO better named identifier
        if channel == 0:
            layout = self.ids.layout0
            label = self.ids.play0
        elif channel == 1:
            layout = self.ids.layout1
            label = self.ids.play1
        else:
            logger.warning("invalid channel")
            return

        if self.is_browsing[(channel + 1) % 2]:
            self.stop_browsing((channel + 1) % 2)

        self.temp_widget_tree[channel] = label
        layout.remove_widget(label)
        layout.add_widget(self.file_browser)
        self.is_browsing[channel] = True
        self.cur_browser = channel

    def stop_browsing(self, channel: int) -> None:
        if not self.is_browsing[channel]:
            logger.info("not browsing at the moment")
            return

        if channel == 0:
            layout = self.ids.layout0
        elif channel == 1:
            layout = self.ids.layout1
        else:
            logger.warning("invalid channel")
            return

        layout.remove_widget(layout.children[0])  # TODO: dynamic implementation with id
        layout.add_widget(self.temp_widget_tree[channel])
        self.is_browsing[channel] = False


class GUIApp(App):
    def build(self):
        return GUI()

