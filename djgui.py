from scipy.io import wavfile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Line, Color
from kivy.core.window import Window
from kivy.clock import Clock
from numpy import mean


class AudioVisualizer(Widget):
    wav_data = ListProperty([])
    color_deck2 = ListProperty([217/256, 121/256, 37/256])

    def __init__(self, **kwargs):
        super(AudioVisualizer, self).__init__(**kwargs)
        self.abs_pos = [0, 0]
        self.abs_size = [0, 0]
        self.color_deck1 = [171 / 256, 26 / 256, 37 / 256]

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)


        with self.canvas:
            Color(rgb=self.color_deck1)
            #Color(1, 0, 0.5)
            self.line = Line(width = 1)


    def _update_pos(self, instance, value):
        self.abs_pos = instance.pos
        print("new pos: " + str(self.abs_pos))

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'w':
            raw_data = wavfile.read('/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav')[1]
            new_wav_data = []
            for x in raw_data[::50]:
                new_wav_data.append(abs(x[0]))
            self.wav_data = new_wav_data
        return True

    def _update_size(self, instance, value):
        self.abs_size = instance.size

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
    color_font = ListProperty([239/256, 231/256, 190/256])
    color_widget = ListProperty([0/256, 38/256, 53/256])


    def __init__(self, **kwargs):
        super(LabelWithBackground, self).__init__(**kwargs)



class DJGUI(BoxLayout):
    def __init__(self, **kwargs):
        super(DJGUI, self).__init__(**kwargs)
        self.ids.av_l.bind(size=self.ids.av_l._update_size, pos=self.ids.av_l._update_pos)
        self.ids.av_r.bind(size=self.ids.av_r._update_size, pos=self.ids.av_r._update_pos)
    #-----------------------------------Properties------------------------------------#
    # GUI globals
    is_browsing = ObjectProperty(0)  # 0 => no browser, 1 => browser on deck 1, 2 => browser on deck 2
    color_background = ListProperty([1/256, 52/256, 64/256])

    # Track Infos
    title = ObjectProperty(["Pineapple Thief - Threatening War ", "Nirvana - Come As You Are"])
    bpm = StringProperty(["120bpm", "78bpm"])
    time = StringProperty(["1:45/3:05", "17:04/32:00"])
    path = ObjectProperty(["path1", "path2"])
    track_visual_data = ObjectProperty([[1, 2, 3], [9, 0, 1, 3]])

    # Current State
    position = ObjectProperty([10, 5])  #in sec
    pitch = ObjectProperty([0, -0.2])
    is_playing = ObjectProperty([True, False])
    is_on_headphone = ObjectProperty([True, False])

class DJGUIApp(App):
    def build(self):
        return DJGUI()


app = DJGUIApp()
#Window.fullscreen = True
Window.size = [600, 300]
app.run()




















#--------backend code-------#
    #def on_path(self, instance, value):
        #raw_data = wavfile.read('/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav')[1]
        #abs_data = []
        #for x in raw_data[::50]:
        #    abs_data.append(abs(x[0]))

        #width = 330
        #chunk_size = int(len(abs_data)/width)
        #mean_data = []
        #for x in range(0, width):
        #    try:
        #        mean_data.append(mean(abs_data[x * chunk_size: (x + 1) * chunk_size]))
        #    except:
        #        pass
        #
        #max_val = max(mean_data)
        #amp = 20
        #for x in range(0, width):
        #    self.line_points.extend([self.visual_pos[0] + x, self.visual_pos[1] - mean_data[x] * amp / max_val, self.visual_pos[0] + x, self.visual_pos[1] + mean_data[x] * amp / max_val])
