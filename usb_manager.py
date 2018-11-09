import subprocess


class USB_Manager():
    def __init__(self):
        self.device_connected = False
        self.new_mountpoint = False
        self.mountpoint = ""

        self.partition_info = ""
        self.system_partition_name = "sda" #has to be hardcoded

        self.update_process_obj = None
        self.is_updating = False

    def analyze_partitions(self):
        for line in self.partition_info.splitlines():
            words = [x.strip() for x in line.split()]
            maj_num = int(words[1].split(sep = ':')[0])
            name = words[0]
            #print(line)
            #print("maj_num: " + str(maj_num) + "name: " + name)
            try:
                mountpoint = words[6]
            except:
                #print("no mounting point")
                continue #has no mounting point
            if maj_num == 8 and (self.system_partition_name not in name):
                self.device_connected = True
                if self.mountpoint == mountpoint:
                    pass
                else:
                    self.mountpoint = mountpoint
                    self.new_mountpoint = True
                return

        self.device_connected = False
        self.mountpoint = ""

    def update_state(self, event):
        #print("call update_state")
        if self.is_updating:
            if self.update_process_obj.poll() != None and self.update_process_obj.poll() != 32: #TODO: return code check
                self.partition_info = self.update_process_obj.communicate()[0]
                #print(self.partition_info)
                self.analyze_partitions()
                self.is_updating = False
        else:
            self.update_process_obj = subprocess.Popen(["lsblk", "-n"], universal_newlines = True, stdout = subprocess.PIPE)
            self.is_updating = True

    #return True if mountpoint is new
    def get_mount_point(self):
        if self.new_mountpoint:
            self.new_mountpoint = False
            return [True, self.mountpoint]
        else:
            return [False, self.mountpoint]
