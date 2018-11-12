# CLEANED UP

from pyo import *
import time
import threading
import logging

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class TrackLoader(threading.Thread):  # TODO maybe use multiprocessing for speed improvement
    def __init__(self, player, path, channel, clear_temp_dir):
        threading.Thread.__init__(self)
        self.clear_temp_dir = clear_temp_dir
        self.player = player
        self.path = path
        self.channel = channel

    def run(self):
        try:
            info = sndinfo(self.path)
        except Exception as e:
            logger.error(e)
            return
        else:
            dur = info[1]

        cur_time = 0.0
        step = 1.0
        is_loading = True
        try:
            if step <= dur:
                self.player.table[self.channel].setSound(self.path, 0, step)
            else:
                logger.info("Track is very short")
                self.player.table[self.channel].setSound(self.path)
                is_loading = False
        except Exception as e:
            logger.error(e)
            return

        while is_loading:
            cur_time += step
            if cur_time + step > dur:
                step = dur - cur_time
                is_loading = False
            stop_time = cur_time + step
            try:
                self.player.table[self.channel].append(self.path, 0, cur_time, stop_time)
            except Exception as e:
                logger.error(e)
            time.sleep(0.000001)

        self.player.title[self.channel] = str(self.path.split("/")[-1:])[:-3]
        self.player.pointer[self.channel].table = self.player.table[self.channel]
        self.player.phasor[self.channel].reset()
        self.player.phasor[self.channel].freq = 0
        self.player.refresh_snd[self.channel] = True
        self.player.start_stop(0)  # TODO manage start_stop external with wait
        self.clear_temp_dir()  # TODO maybe lean somewhere else
