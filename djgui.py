from math import sin
from scipy.io import wavfile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color
from numpy import mean
from math import log

class AudioVisualizer(Widget):


    def __init__(self, **kwargs):
        super(AudioVisualizer, self).__init__(**kwargs)
        raw_data = wavfile.read('/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav')[1]
        data = []
        for x in raw_data:
            data.append(abs(x[0]))

        win_width = 400
        chunk_size = int(len(data)/win_width)
        line_points = []
        for x in range(0, win_width):
            try:
                line_points.append(mean(data[x * chunk_size: (x + 1) * chunk_size]))
            except:
                pass

        line_points = [x * 40 / max(line_points) for x in line_points]

        with self.canvas.after:
            Color(1, 0.5, 1)
            for x in range(0, len(line_points)):
                Line(points=[x, 0, x, line_points[x]], width=1)

class DJGUI(BoxLayout):
    time = StringProperty("0:00/0:00")
    pass

class DJGUIApp(App):
    def build(self):
        return DJGUI()


app = DJGUIApp()

app.run()
