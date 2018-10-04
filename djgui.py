from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class DJGUI(BoxLayout):
    pass

class DJGUIApp(App):
    def build(self):
        return DJGUI()


app = DJGUIApp()

app.run()
