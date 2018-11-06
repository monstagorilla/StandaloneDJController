from scipy.io import wavfile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color
from kivy.core.window import Window
from numpy import mean


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
        with self.canvas:
            self.color_deck = Color()
            self.line = Line(width=1)

    def _update_pos(self, instance, value):
        self.abs_pos = instance.pos
        self.on_wav_data(instance, value)

    def _update_size(self, instance, value):
        self.abs_size = instance.size
        self.on_wav_data(instance, value)

    def on_wav_data(self, instance, value):
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
        line_points = []
        for x in range(0, int(self.width)):
            line_points.extend([self.abs_pos[0] + x, self.abs_pos[1] - mean_data[x] * scaling_factor + self.abs_size[1] / 2,
                                self.abs_pos[0] + x, self.abs_pos[1] + mean_data[x] * scaling_factor + self.abs_size[1] / 2])
        self.line.points = line_points


class LabelWithBackground(Label):
    color_widget = ListProperty([0/256, 38/256, 53/256])

    def __init__(self, **kwargs):
        super(LabelWithBackground, self).__init__(**kwargs)


class DJGUI(BoxLayout):
    def __init__(self, **kwargs):
        super(DJGUI, self).__init__(**kwargs)
        self.ids.av_l.bind(size=self.ids.av_l._update_size, pos=self.ids.av_l._update_pos)
        self.ids.av_r.bind(size=self.ids.av_r._update_size, pos=self.ids.av_r._update_pos)
        self.ids.av_l.color_deck.rgb = self.color_deck1
        self.ids.av_r.color_deck.rgb = self.color_deck2

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)


    #----------------------------------Properties------------------------------------#
    # GUI globals
    is_browsing = ObjectProperty(0)  # 0 => no browser, 1 => browser on deck 1, 2 => browser on deck 2
    color_background = ListProperty([1/256, 52/256, 64/256])
    color_deck1 = ListProperty([171 / 256, 26 / 256, 37 / 256])
    color_deck2 = ListProperty([217/256, 121/256, 37/256])
    color_font = ListProperty([239/256, 231/256, 190/256])

    # Track Infos
    title0 = StringProperty("left")
    title1 = StringProperty("right")
    bpm0 = StringProperty("128")
    bpm1 = StringProperty("70")
    path0 = StringProperty("path0")  # necessary?
    path1 = StringProperty("path1")


    # Current State
    position = ObjectProperty([10, 5])  #in sec
    time = StringProperty(["1:45/3:05", "17:04/32:00"])
    pitch = ObjectProperty([0, -0.2])
    is_playing = ObjectProperty([True, False])
    is_on_headphone = ObjectProperty([True, False])

    def update_gui(self, track0=None, track1=None, position=None, pitch=None, is_playing=None, is_on_headphone=None):
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
        if position is not None:
            self.position = position
        if pitch is not None:
            self.pitch = pitch
        if is_playing is not None:
            self.is_playing = is_playing
        if is_on_headphone is not None:
            self.is_on_headphone = is_on_headphone

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
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

            return True


class DJGUIApp(App):
    def build(self):
        return DJGUI()


if __name__ == '__main__':
    app = DJGUIApp()
    #Window.fullscreen = True
    Window.size = [600, 300]
    app.run()