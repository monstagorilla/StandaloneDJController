from usb_manager import USB_Manager
from decoder import Decoder
import os
import shutil
from kivy.uix.filechooser import FileChooserListView
from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.app import App
from kivy.core.window import Window

Builder.load_string('''
<FileBrowser>:
    rootpath: root.root_path
    filters: ["*.mp3", "*.wav"]
''')


class FileBrowser(FileChooserListView):
    root_path = StringProperty(os.path.expanduser("~/Music"))
    def __init__(self):
        super(FileChooserListView, self).__init__()
        self.path_root = ""
        self.path_temp = os.path.expanduser("~/temp_standalone_dj_controller")

        self.usb = USB_Manager()
        self.decoder = Decoder(self.path_temp, self, self.clear_temp_dir)

        # init temp dir
        if os.path.isdir(self.path_temp):
            self.clear_temp_dir()
        else:
            os.mkdir(self.path_temp)

        self.dir_list = []
        self.track_list = []
        self.index = 0
        self.dir_lvl = 0

        if len(self._items) > 0:
            self._items[0].is_selected = True

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def clear_temp_dir(self):
        for the_file in os.listdir(self.path_temp):
            file_path = os.path.join(self.path_temp, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)

    def update_mountpoint(self, event):
        result = self.usb.get_mount_point()
        #print(result)
        if result[0] or not self.usb.device_connected: #mountpoint is a new one
            #update paths 'cause of new device
            self.path_root = result[1]
            self.path = self.path_root
            self.refresh_list_view()

    def get_codec(self, path):
        if len(path) < 4:
            return
        return path[-4:]

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'down':
            count = len(self._items)
            has_selected = False
            for i in range(0, count):
                if self._items[i].is_selected:
                    has_selected = True
                    if i < count - 1:
                        self._items[i].is_selected = False
                        self._items[i + 1].is_selected = True
                    break
            if not has_selected:
                self._items[0].is_selected = True
        elif keycode[1] == 'up':
            count = len(self._items)
            has_selected = False
            for i in range(0, count):
                if self._items[i].is_selected:
                    has_selected = True
                    if i > 0:
                        self._items[i].is_selected = False
                        self._items[i - 1].is_selected = True
                    break
            if not has_selected:
                self._items[count - 1].is_selected = True

        elif keycode[1] == 'enter':
            for x in self._items:
                if x.is_selected:
                    if self.file_system.is_dir(x.path):
                        self.path = x.path
                        if len(self._items) > 0:
                            self._items[0].is_selected = True

                    else:
                        print("load_track")
        elif keycode[1] == 'left':
            if self.path != self.rootpath:
                self.path = "/".join(self.path.split("/")[:-1])




class FileApp(App):
    def build(self) -> FileBrowser:
        return FileBrowser()

FileApp().run()