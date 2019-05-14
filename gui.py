from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.label import Label
from player import Player
from file_browser import FileBrowser
from kivy.clock import Clock
import logging
from pyo import *
from multiprocessing import Pipe
from gui_classes import Track
import numpy
import math

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class LabelWithBackground(Label):
    color_widget = ListProperty([0/256, 38/256, 53/256])

    def __init__(self, **kwargs) -> None:  # TODO not needed?
        super(LabelWithBackground, self).__init__(**kwargs)


class GUI(BoxLayout):
    def __init__(self, **kwargs) -> None:
        super(GUI, self).__init__(**kwargs)
        # update size and pos of AudioVisualizer
        self.ids.av_l.bind(size=self.ids.av_l.update_size, pos=self.ids.av_l.update_pos)
        self.ids.av_r.bind(size=self.ids.av_r.update_size, pos=self.ids.av_r.update_pos)
        self.ids.av_l.color_deck0.rgb = self.color_deck_l0
        self.ids.av_l.color_deck1.rgb = self.color_deck_l1
        self.ids.av_r.color_deck0.rgb = self.color_deck_r0
        self.ids.av_r.color_deck1.rgb = self.color_deck_r1

        # init keyboard input
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        # Connections to player
        self.rx_gui_update, tx_gui_update = Pipe(duplex=False)
        self.rx_new_track, tx_new_track = Pipe(duplex=False)  # pipe to update gui once when track loaded
        self.rx_wav_data, tx_wav_data = Pipe(duplex=False)  # pipe to update gui once when track loaded
        rx_player_fn, self.tx_player_fn = Pipe(duplex=False)  # pipe to call player functions

        # Objects
        self.player = Player(tx_gui_update, tx_new_track, rx_player_fn, tx_wav_data)
        self.player.start()
        self.file_browser = FileBrowser()
        self.cur_browser = 0
        self.temp_widget_tree = [None, None]
        self.is_browsing = [False, False]
        self.wav_data = [None, None]

        # clock scheduling
        Clock.schedule_interval(self.handler_player, 0.001)  # TODO choose good interval time
        Clock.schedule_interval(self.handler_new_track, 0.1)  # TODO choose good interval time
        Clock.schedule_interval(self.handler_wav_data, 0.1)

    # ----------------------------------Properties------------------------------------ #
    # GUI globals
    is_browsing = ObjectProperty(0)  # 0 => no browser, 1 => browser on deck 1, 2 => browser on deck 2
    color_background = ListProperty([1/256, 52/256, 64/256])
    color_deck_l0 = ListProperty([171 / 256, 26 / 256, 37 / 256])
    color_deck_l1 = ListProperty([80 / 256, 10 / 256, 15 / 256])
    color_deck_r0 = ListProperty([217/256, 121/256, 37/256])
    color_deck_r1 = ListProperty([100/256, 60/256, 15/256])
    color_font = ListProperty([239/256, 231/256, 190/256])
    color_vu_green = ListProperty([0, 150 / 256, 0])
    color_vu_yellow = ListProperty([1, 1, 0])
    color_vu_red = ListProperty([1, 0, 0])

    # TODO correct default values
    # Track Info
    title0 = StringProperty("")
    title1 = StringProperty("")
    bpm0 = StringProperty("")
    bpm1 = StringProperty("")

    # Current State
    time0 = StringProperty("0:00/0:00")
    time1 = StringProperty("0:00/0:00")
    position0 = NumericProperty(0)
    position1 = NumericProperty(0)
    pitch0 = StringProperty("+0.0%")
    pitch1 = StringProperty("+0.0%")
    is_playing0 = BooleanProperty(False)
    is_playing1 = BooleanProperty(False)
    is_on_headphone0 = BooleanProperty(False)
    is_on_headphone1 = BooleanProperty(False)
    volume0 = NumericProperty(0)
    volume1 = NumericProperty(0)

    def handler_new_track(self, dt):
        return
        if self.rx_new_track.poll():
            d = self.rx_new_track.recv()
            if len(d) != 2:
                logger.error("corrupt data")
                return
            channel = d[0]
            if channel == 0:
                self.update_gui(track0=d[1])
            elif channel == 1:
                self.update_gui(track1=d[1])

    def handler_wav_data(self, dt) -> None:
        return
        if self.rx_wav_data.poll():
            wav_data, channel = self.rx_wav_data.recv()
            self.wav_data[channel] = wav_data
            if channel == 0:
                self.ids.   av_l.wav_data = self.get_visual_data(channel, self.ids.av_l.size[0])
                #self.ids.av_l.wav_data = []
            elif channel == 1:
                self.ids.av_r.wav_data = self.get_visual_data(channel, self.ids.av_r.size[0])
               # self.ids.av_r.wav_data = []

    # width in px, length in samples, pos in samples,
    def get_visual_data(self, channel: int, width: int, length: int = None, pos: int = None):  # TODO maybe use future
        return
        if self.wav_data[channel] is None:
            return
        if length is None or pos is None:
            wav_data_slice = numpy.array(self.wav_data[channel])
        else:
            wav_data_slice = numpy.zeros(length)
            temp = numpy.array(self.wav_data[channel][pos - round(length / 2) if 0 <= pos - round(length / 2) else 0:
                                                      pos + round(length / 2) if pos + round(length / 2) <
                                                                                 len(self.wav_data[channel]) else
                                                      len(self.wav_data[channel])])
            wav_data_slice[int(length / 2) - pos: len(self.wav_data[channel]) - pos + int(length / 2)] = temp

        if width > 0:
            chunk_size = int(len(wav_data_slice) / width)
        else:
            logger.error("width = 0 -> cannot divide")
            return
        mean_data = []
        for x in range(0, int(width)):
            try:
                mean_data.append(numpy.mean(wav_data_slice[x * chunk_size: (x + 3) * chunk_size]))
            except Exception as e:
                logger.warning(e)
        return mean_data

    def handler_player(self, dt):
        if self.rx_gui_update.poll():
            d = self.rx_gui_update.recv()
            self.update_gui(position0=d[0], position1=d[1], time0=d[2], time1=d[3], pitch0=d[4], pitch1=d[5],
                            is_playing0=d[6], is_playing1=d[7], is_on_headphone0=d[8], is_on_headphone1=d[9],
                            volume0=d[10], volume1=d[11])

    def update_gui(self, track0: Track = None, track1: Track = None, position0: float = None, position1: float = None,
                   time0: str = None, time1: str = None, pitch0: str = None, pitch1: str = None,
                   is_playing0: bool = None, is_playing1: bool = None, is_on_headphone0: bool = None,
                   is_on_headphone1: bool = None, volume0: float = None,
                   volume1: float = None) -> None:
        if track0 is not None:
            self.title0 = track0.title
            self.bpm0 = track0.bpm
        if track1 is not None:
            self.title1 = track1.title
            self.bpm1 = track1.bpm
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
        if volume0 is not None:
            self.volume0 = volume0
        if volume1 is not None:
            self.volume1 = volume1

    def _keyboard_closed(self) -> None:
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers) -> bool:
        if keycode[1] == "b":
            if self.is_browsing[0]:
                self.stop_browsing(0)
            else:
                self.start_browsing(0)
        elif keycode[1] == "n":
            if self.is_browsing[1]:
                self.stop_browsing(1)
            else:
                self.start_browsing(1)
        # start_stop
        elif keycode[1] == "v":
            self.tx_player_fn.send(("start_stop", 0))
        elif keycode[1] == "m":
            self.tx_player_fn.send(("start_stop", 1))

        # normal eq left
        elif keycode[1] == "e":
            self.tx_player_fn.send(("set_eq", ["high", 0, 0]))
        elif keycode[1] == "d":
            self.tx_player_fn.send(("set_eq", ["mid", 0, 0]))
        elif keycode[1] == "c":
            self.tx_player_fn.send(("set_eq", ["low", 0, 0]))
        #  mute eq left
        elif keycode[1] == "w":
            self.tx_player_fn.send(("set_eq", ["high", 0, -1]))
        elif keycode[1] == "s":
            self.tx_player_fn.send(("set_eq", ["mid", 0, -1]))
        elif keycode[1] == "x":
            self.tx_player_fn.send(("set_eq", ["low", 0, -1]))
        # normal eq right
        elif keycode[1] == "i":
            self.tx_player_fn.send(("set_eq", ["high", 1, 0]))
        elif keycode[1] == "k":
            self.tx_player_fn.send(("set_eq", ["mid", 1, 0]))
        elif keycode[1] == ",":
            self.tx_player_fn.send(("set_eq", ["low", 1, 0]))
        # mute eq right
        elif keycode[1] == "o":
            self.tx_player_fn.send(("set_eq", ["high", 1, -1]))
        elif keycode[1] == "l":
            self.tx_player_fn.send(("set_eq", ["mid", 1, -1]))
        elif keycode[1] == ".":
            self.tx_player_fn.send(("set_eq", ["low", 1, -1]))

        # set pitch left
        elif keycode[1] == "r":
            self.tx_player_fn.send(("set_pitch", [0.9, 0]))
        elif keycode[1] == "f":
            self.tx_player_fn.send(("set_pitch", [1.1, 0]))
        # set pitch right
        elif keycode[1] == "u":
            self.tx_player_fn.send(("set_pitch", [0.9, 1]))
        elif keycode[1] == "j":
            self.tx_player_fn.send(("set_pitch", [1.1, 1]))

        # do jump left
        elif keycode[1] == "t":
            self.tx_player_fn.send(("jump", [-0.1, 0]))
        elif keycode[1] == "g":
            self.tx_player_fn.send(("jump", [0.1, 0]))
        # do jump right
        elif keycode[1] == "z":
            self.tx_player_fn.send(("jump", [-0.1, 1]))
        elif keycode[1] == "h":
            self.tx_player_fn.send(("jump", [0.1, 1]))

        # browsing
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
                            self.tx_player_fn.send(("load_track", [x.path, self.cur_browser]))
                            break
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

    def on_volume0(self, instance, value) -> None:
        self.on_volume(self.ids.vu0.children, int(value * len(self.ids.vu0.children)))

    def on_volume1(self, instance, value) -> None:
        self.on_volume(self.ids.vu1.children, int(value * len(self.ids.vu1.children)))

    def on_volume(self, children: list, index_limit: int):
        if index_limit >= len(children):
            logger.error("invalid index")
            return
        for i in range(0, len(children)):
            if i >= index_limit:
                children[i].color_widget = [0, 0, 0]
            else:
                children[i].color_widget = children[i].color

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

