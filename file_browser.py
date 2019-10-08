# CLEAN
from usbmanager import USBManager
from kivy.uix.filechooser import FileChooserListView
from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock
import ffmpeg
import logging
import sys
import config

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(config.logging_level)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)

# TODO maybe allow all codecs
Builder.load_string('''
<FileBrowser>:
    id: fb
    rootpath: root.root_path
    #filters: ["*.mp3", "*.wav"]  
''')


class FileBrowser(FileChooserListView):
    root_path = StringProperty("")

    def __init__(self):
        super(FileChooserListView, self).__init__()
        self.usb_manager = USBManager()

        Clock.schedule_interval(self.update_mount_point, 0.1)  # TODO choose good interval time

    def update_mount_point(self, dt):
        result = self.usb_manager.get_mount_point()
        if not result:
            logger.error("no result")
            return
        if result[0] or not self.usb_manager.device_connected:  # mount point is a new one
            # update paths 'cause of new device
            self.root_path = result[1]
            self.path = self.root_path

    def get_codec(self, path: str) -> str:  # TODO maybe somewhere else,
        try:
            codec = ffmpeg.probe(path)["format"]["format_name"]
        except Exception as e:
            logger.error(e)
            # raise
            return ""  # TODO improve error handling
        else:
            return codec
