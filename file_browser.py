# CLEANED UP

from usbmanager import USBManager
import os
import shutil
from kivy.uix.filechooser import FileChooserListView
from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock

Builder.load_string('''
<FileBrowser>:
    id: fb
    rootpath: root.root_path
    #bfilters: ["*.mp3", "*.wav"]
''')


class FileBrowser(FileChooserListView):
    # root_path = StringProperty(os.path.expanduser("~/Music"))
    root_path = StringProperty("")

    def __init__(self):
        super(FileChooserListView, self).__init__()
        self.usb_manager = USBManager()

        Clock.schedule_interval(self.update_mount_point, 0.1)  # TODO choose good interval time

    def update_mount_point(self, dt):
        result = self.usb_manager.get_mount_point()
        if result[0] or not self.usb_manager.device_connected:  # mount point is a new one
            # update paths 'cause of new device
            self.root_path = result[1]
            self.path = self.root_path

    def get_codec(self, path):  # TODO maybe somewhere else
        if len(path) < 3:
            return
        return path[-3:]
