from pyo import *
import time
import threading


class TrackLoader(threading.Thread):  # TODO maybe use multiprocessing for speed improvement
    def __init__(self, player, path, channel, clear_temp_dir):
        threading.Thread.__init__(self)
        self.clear_temp_dir = clear_temp_dir
        self.player = player
        self.path = path
        self.channel = channel

    def run(self):
        info = sndinfo(self.path)
        dur = info[1]
        cur_time = 0.0
        step = 1.0
        if step <= dur:
            #self.player.table[self.channel] = SndTable()
            self.player.table[self.channel].setSound(self.path, 0, step)
            self.player.mono_table[self.channel].setSound(self.path, 0, step)
        else:
            print("track too short") #TODO implement better solution
        cur_time = step
        flag = True
        while flag:
            if cur_time + step > dur:
                step = dur - cur_time
                flag = False
            stop_time = cur_time + step
            try:
                self.player.table[self.channel].append(self.path, 0, cur_time, stop_time)
                self.player.mono_table[self.channel].append(self.path, 0, cur_time, stop_time)
            except:
                print("error while loading track")
            cur_time += step
            time.sleep(0.000001)

        temp_str = str(self.path.split("/")[-1:])
        self.player.title[self.channel] = temp_str[:-3]
        self.player.pointer[self.channel].table = self.player.table[self.channel]
        self.player.phasor[self.channel].reset()
        self.player.phasor[self.channel].freq = 0
        self.player.refresh_snd[self.channel] = True
        self.player.start_stop(0)
        self.clear_temp_dir()
