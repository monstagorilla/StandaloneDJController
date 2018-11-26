# CLEAN

import subprocess
import logging
import sys
from kivy.clock import Clock

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class USBManager:
    def __init__(self):
        self.device_connected = False
        self.new_mount_point = False
        self.mount_point = ""
        self.partition_info = ""
        self.system_partition_name = "sda"  # has to be hardcoded
        self.update_process_obj = None
        self.is_updating = False

        Clock.schedule_interval(self.update_state, 1)

    def analyze_partitions(self):
        for line in self.partition_info.splitlines():
            words = [x.strip() for x in line.split()]
            maj_num = int(words[1].split(sep=':')[0])
            name = words[0]
            try:
                mount_point = words[6]
            except:
                continue  # has no mounting point
            if maj_num == 8 and (self.system_partition_name not in name):
                self.device_connected = True
                if self.mount_point != mount_point:
                    self.mount_point = mount_point
                    self.new_mount_point = True
                return

        # no device connected
        self.device_connected = False
        self.mount_point = ""

    def update_state(self, event):
        if self.is_updating:
            # TODO: return code check
            if self.update_process_obj.poll() is not None and self.update_process_obj.poll() != 32:
                self.partition_info = self.update_process_obj.communicate()[0]
                self.analyze_partitions()
                self.is_updating = False
        else:
            self.update_process_obj = subprocess.Popen(["lsblk", "-n"], universal_newlines=True, stdout=subprocess.PIPE)
            self.is_updating = True

    # return True if mount_point is new
    def get_mount_point(self):
        if self.new_mount_point:
            self.new_mount_point = False
            return [True, self.mount_point]
        else:
            return [False, self.mount_point]
