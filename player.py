from pyo import *
import logging
import multiprocessing
import sys
from kivy.clock import Clock
from multiprocessing.connection import Connection
import track_loading
import concurrent.futures
from gui_classes import Track
import ffmpeg

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class Player(multiprocessing.Process):  # TODO shared memory?
    def __init__(self, tx_gui: Connection, tx_new_track: Connection, rx_width: Connection, rx_player_fn: Connection) -> None:
        super(Player, self).__init__()
        # Pipes
        self.tx_gui = tx_gui
        self.tx_new_track = tx_new_track
        self.rx_width = rx_width
        self.rx_player_fn = rx_player_fn

        # Properties
        self.server = Server()
        self.server.setInOutDevice(8)
        self.server.boot()
        self.server.start()
        self.track = [Track(), Track()]
        self.is_playing = [False, False]
        self.is_on_headphone = [False, False]
        self.refresh_snd = [False, False]#
        self.shared_table_p = [SndTable(), SndTable()]

        # Audio Modules
        self.phasor = [Phasor(freq=0), Phasor(freq=0)]  # TODO prevent from looping
        self.pointer = [Pointer(table=self.shared_table_p[0], index=self.phasor[0], mul=0.3),
                        Pointer(table=self.shared_table_p[1], index=self.phasor[1], mul=0.3)]  # TODO why mul != 1?
        self.pitch = [1, 1]
        self.lowEq = [EQ(input=self.pointer[0], boost=1, freq=125, q=1, type=1),  # TODO good choice for frequencies?
                      EQ(input=self.pointer[1], boost=1, freq=125, q=1, type=1)]
        self.midEq = [EQ(input=self.lowEq[0], boost=1, freq=1200, q=0.5, type=0),
                      EQ(input=self.lowEq[1], boost=1, freq=1200, q=0.5, type=0)]
        self.highEq = [EQ(input=self.midEq[0], boost=1, freq=4000, q=1, type=2),
                       EQ(input=self.midEq[1], boost=1, freq=4000, q=1, type=2)]
        self.mixer = Mixer(outs=1, chnls=2)
        self.mixer.addInput(0, self.highEq[0])
        self.mixer.addInput(1, self.highEq[1])
        self.mixer.setAmp(0, 0, 1)  # TODO controlling volume
        self.mixer.setAmp(1, 0, 1)
        self.mainVolume = Mixer(outs=1, chnls=2)
        self.mainVolume.addInput(0, self.mixer[0])
        self.mainVolume.setAmp(0, 0, 1)
        self.mainVolume.out(1)
        self.volume_meter_0 = PeakAmp(self.highEq[0], function=self.get_volume0)
        self.volume_meter_1 = PeakAmp(self.highEq[1], function=self.get_volume1)
        self.volume = [0, 0]
        Clock.schedule_interval(self.refresh_gui, 0.001)
        Clock.schedule_interval(self.handler_width, 1)
        Clock.schedule_interval(self.handler_player_fn, 0.001)


        self.visual_width = 0

        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)

    def get_volume0(self, *args):
        self.volume[0] = args[0]

    def get_volume1(self, *args):
        self.volume[1] = args[0]

    def handler_player_fn(self, dt):
        if self.rx_player_fn.poll():
            fn, args = self.rx_player_fn.recv()
            if fn == "start_stop":
                self.start_stop(args)
            elif fn == "set_pitch":
                self.set_pitch(args[0], args[1])
            elif fn == "jump":
                self.jump(args[0], args[1])
            elif fn == "set_eq":
                if args[0] == "high":
                    self.set_eq(self.highEq[args[1]], args[2])  # args[1] == channel, args[2] == value
                elif args[0] == "mid":
                    self.set_eq(self.midEq[args[1]], args[2])
                elif args[0] == "low":
                    self.set_eq(self.lowEq[args[1]], args[2])
            elif fn == "load_track":
                if self.is_playing[args[1]]:
                    logger.warning("is playing")
                    return
                info = float(ffmpeg.probe(args[0])["format"]["duration"]) * 44100
                self.shared_table_p[args[1]] = SharedTable(["/sharedl{}".format(args[1]), "/sharedr{}".format(args[1])],
                                                           True, int(info))
                future = self.executor.submit(track_loading.load, args[0], args[1])
                future.add_done_callback(self.set_new_track)

    def handler_width(self, dt):
        if self.rx_width.poll():
            self.visual_width = self.rx_width.recv()

    def refresh_gui(self, dt):
        if not self.is_playing[0] and not self.is_playing[1]:
            return
        tx_data = []
        if self.is_playing[0] and self.is_playing[1]:
            tx_data = [self.phasor[0].get(), self.phasor[1].get(), self.pos_to_str(0), self.pos_to_str(1),
                       self.pitch_to_str(0), self.pitch_to_str(1), self.is_playing[0], self.is_playing[1],
                       self.is_on_headphone[0], self.is_on_headphone[1],self.volume[0], self.volume[1]]
        elif self.is_playing[0]:
            tx_data = [self.phasor[0].get(), None, self.pos_to_str(0), None,
                       self.pitch_to_str(0), None, self.is_playing[0], None,
                       self.is_on_headphone[0], None, self.volume[0], None]
        elif self.is_playing[1]:
            tx_data = [None, self.phasor[1].get(), None, self.pos_to_str(1),
                       None, self.pitch_to_str(1), None, self.is_playing[1],
                       None, self.is_on_headphone[1], None, self.volume[1]]
        self.tx_gui.send(tx_data)

    def set_new_track(self, future):
        result = future.result()
        path = result[0]
        channel = result[1]
        if self.shared_table_p is None:
            logger.error("Loading Failed")
            return
        # TODO very unsafe
        self.track[channel] = Track(title=str(path.split("/")[-1:][0].split(".")[:-1][0]), bpm="120 bpm", path=path)
        self.phasor[channel].reset()
        self.phasor[channel].freq = 0
        self.pointer[channel].table = self.shared_table_p[channel]
        #self.tx_new_track.send([channel, self.track[channel], visual_data])


    #def get_bpm  # TODO impl fn get_bpm

    def start_stop(self, channel: int) -> None:
        if self.is_playing[channel]:
            self.phasor[channel].freq = 0
            self.is_playing[channel] = False
            logger.info("stopped playback on channel {}".format(channel))
        else:
            if not self.shared_table_p[channel]:
                logger.error("no track loaded")
                return
            self.phasor[channel].freq = self.shared_table_p[channel].getRate() * self.pitch[channel]
            self.is_playing[channel] = True
            logger.info("started playback on channel {}".format(channel))

    def set_pitch(self, value: int, channel: int) -> None:
        self.pitch[channel] = value
        if self.shared_table_p[channel] is not None:
            self.phasor[channel].freq = value * self.shared_table_p[channel].getRate()
        else:
            logger.info("no track loaded")

    def set_position(self, position: float, channel: int) -> None:  # TODO not using this function yet
        self.phasor[channel].reset()
        self.phasor[channel].phase = position

    def jump(self, diff: float, channel: int) -> None:
        if 0 <= self.phasor[channel].get() + diff <= 1:
            self.phasor[channel].phase += diff
        else:
            logger.info("tried to jump out of bounds")

    # TODO universal system of input values maybe between -1 and 1
    def set_eq(self, equalizer: EQ, value: float) -> None:
        if value > 0:
            value /= 10  # weaker increasing than lowering
        equalizer.boost = value * 40  # max lowering 40dB

    def pos_to_str(self, channel: int):
        sec, dur = (self.phasor[channel].phase * self.shared_table_p[channel].getDur(), self.shared_table_p[channel].getDur())
        return "{}:{}/{}:{}".format(str(int(sec / 60)), str(int(sec) % 60).zfill(2), str(int(dur / 60)),
                                    str(int(dur) % 60).zfill(2))

    def pitch_to_str(self, channel: int):
        return "{}{}%".format(("+" if self.pitch[channel] >= 1 else ""), (self.pitch[channel] - 1) * 100)




