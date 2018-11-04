from scipy.io import wavfile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Line, Color
from kivy.core.window import Window
from numpy import mean


class AudioVisualizer(Widget):
    def __init__(self, **kwargs):
        super(AudioVisualizer, self).__init__(**kwargs)
        with self.canvas.before:
            self.line = Line(width = 1)

    def _update_line(self, instance, value):
        self.line.points = [instance.pos[0], instance.pos[1], instance.pos[0] + 10, instance.pos[1] + 10]



class LabelWithBackground(Label):
    color_font = ListProperty([239/256, 231/256, 190/256])
    color_widget = ListProperty([0/256, 38/256, 53/256])


    def __init__(self, **kwargs):
        super(LabelWithBackground, self).__init__(**kwargs)



class DJGUI(BoxLayout):
    def __init__(self, **kwargs):
        super(DJGUI, self).__init__(**kwargs)
        self.ids.av_l.bind(size=self.ids.av_l._update_line, pos=self.ids.av_l._update_line)
        self.ids.av_r.bind(size=self.ids.av_r._update_line, pos=self.ids.av_r._update_line)


    #-----------------------------------Properties------------------------------------#
    # GUI globals
    is_browsing = ObjectProperty(0)  # 0 => no browser, 1 => browser on deck 1, 2 => browser on deck 2
    color_background = ListProperty([1/256, 52/256, 64/256])
    color_deck1 = ListProperty([171/256, 26/256, 37/256])
    color_deck2 = ListProperty([217/256, 121/256, 37/256])

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
