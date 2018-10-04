from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty

class DJGUI(BoxLayout):
    time = StringProperty("0:00/0:00")
    pass

class DJGUIApp(App):
    def build(self):
        return DJGUI()


app = DJGUIApp()

app.run()
