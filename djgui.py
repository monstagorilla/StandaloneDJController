from scipy.io import wavfile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color
from kivy.core.window import Window
from numpy import mean

class AudioVisualizer(Widget):
    some_val = ObjectProperty([])
    def __init__(self, **kwargs):
        super(AudioVisualizer, self).__init__(**kwargs)
        raw_data = wavfile.read('/home/monstagorilla/Music/Indigo (Alex Niggemann Remix).wav')[1]
        abs_data = []
        for x in raw_data[::50]:
            abs_data.append(abs(x[0]))

        width = 250
        chunk_size = int(len(abs_data)/width)
        mean_data = []
        for x in range(0, width):
            try:
                mean_data.append(mean(abs_data[x * chunk_size: (x + 1) * chunk_size]))
            except:
                pass

        max_val = max(mean_data)
        amp = 20
        self.line_points = []
        for x in range(0, width):
            self.line_points.extend([300 + x, 400, 300 + x, 400 + mean_data[x] * amp / max_val])

        with self.canvas.after:
            Color(1, 0.5, 1)
            Line(points=self.line_points)



class DJGUI(BoxLayout):
    time = StringProperty(["0:00/0:00", "0:00/0:00"])
    track_name = StringProperty(["Pineapple Thief - Threatening War ", "Nirvana - Come A You Are"])
    bpm = StringProperty(["122", "79"])



class DJGUIApp(App):
    def build(self):
        return DJGUI()


app = DJGUIApp()
#Window.fullscreen = True


app.run()
