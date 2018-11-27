# CLEAN
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


class Player(multiprocessing.Process):
    def __init__(self, tx_update_gui: Connection, tx_new_track: Connection, rx_player_fn: Connection, tx_wav_data) -> None:
        super(Player, self).__init__()
        # Pipes
        self.tx_update_gui = tx_update_gui
        self.tx_new_track = tx_new_track
        self.rx_player_fn = rx_player_fn
        self.tx_wav_data = tx_wav_data

        # Objects
        self.server = Server()
        self.server.setInOutDevice(8)
        self.server.boot()
        self.server.start()
        self.track = [Track(), Track()]
        self.is_playing = [False, False]
        self.is_on_headphone = [False, False]
        self.is_loading = [False, False]
        self.refresh_snd = [False, False]
        self.shared_table_p = [SndTable(), SndTable()]
        self.pitch = [1, 1]
        self.volume = [0, 0]
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)

        # Audio Modules
        self.phasor = [Phasor(freq=0), Phasor(freq=0)]  # TODO prevent from looping, ask muvlon
        self.pointer = [Pointer(table=self.shared_table_p[0], index=self.phasor[0], mul=1),
                        Pointer(table=self.shared_table_p[1], index=self.phasor[1], mul=1)]
        self.lowEq = [EQ(input=self.pointer[0], boost=1, freq=125, q=1, type=1),  # TODO good choice for frequencies?
                      EQ(input=self.pointer[1], boost=1, freq=125, q=1, type=1)]
        self.midEq = [EQ(input=self.lowEq[0], boost=1, freq=1200, q=0.5, type=0),
                      EQ(input=self.lowEq[1], boost=1, freq=1200, q=0.5, type=0)]
        self.highEq = [EQ(input=self.midEq[0], boost=1, freq=4000, q=1, type=2),
                       EQ(input=self.midEq[1], boost=1, freq=4000, q=1, type=2)]
        self.mixer = Mixer(outs=1, chnls=2)
        self.mixer.addInput(0, self.highEq[0])
        self.mixer.addInput(1, self.highEq[1])
        self.mixer.setAmp(0, 0, 1)
        self.mixer.setAmp(1, 0, 1)
        self.mainVolume = Mixer(outs=1, chnls=2)
        self.mainVolume.addInput(0, self.mixer[0])
        self.mainVolume.setAmp(0, 0, 1)
        self.mainVolume.out(1)
        self.volume_meter_0 = PeakAmp(self.highEq[0], function=self.get_volume0)
        self.volume_meter_1 = PeakAmp(self.highEq[1], function=self.get_volume1)

        # clock scheduling
        Clock.schedule_interval(self.refresh_gui, 0.001)
        Clock.schedule_interval(self.handler_player_fn, 0.001)

    def get_volume0(self, *args):
        if len(args) != 1:
            logger.error("no args")
            return
        self.volume[0] = args[0]

    def get_volume1(self, *args):
        if len(args) != 1:
            logger.error("no args")
            return
        self.volume[1] = args[0]

    def handler_player_fn(self, dt) -> None:
        if self.rx_player_fn.poll():
            fn, args = self.rx_player_fn.recv()
            if fn == "start_stop":
                if args is None:
                    logger.error("no args")
                    return
                self.start_stop(args)
            elif fn == "set_pitch":
                if len(args) != 2:
                    logger.error("wrong number of args")
                    return
                self.set_pitch(args[0], args[1])
            elif fn == "jump":
                if len(args) != 2:
                    logger.error("wrong number of args")
                    return
                self.jump(args[0], args[1])
            elif fn == "set_eq":
                if len(args) != 3:
                    logger.error("wrong number of args")
                    return
                if args[0] == "high":
                    self.set_eq(self.highEq[args[1]], args[2])  # args[1] == channel, args[2] == value
                elif args[0] == "mid":
                    self.set_eq(self.midEq[args[1]], args[2])
                elif args[0] == "low":
                    self.set_eq(self.lowEq[args[1]], args[2])
            elif fn == "load_track":
                if len(args) != 2:
                    logger.error("wrong number of args")
                    return
                if self.is_loading[args[1]]:
                    logger.info("is already loading")
                    return
                elif self.is_playing[args[1]]:
                    logger.info("is playing")
                    return
                info = float(ffmpeg.probe(args[0])["format"]["duration"]) * 44100
                self.shared_table_p[args[1]] = SharedTable(["/sharedl{}".format(args[1]), "/sharedr{}".format(args[1])],
                                                           True, int(info))
                future = self.executor.submit(track_loading.load, args[0], args[1], self.tx_wav_data)
                self.is_loading[args[1]] = True
                future.add_done_callback(self.set_new_track)

    def refresh_gui(self, dt):
        try:
            tx_data = [self.phasor[0].get(), self.phasor[1].get(), self.pos_to_str(0), self.pos_to_str(1),
                       self.pitch_to_str(0), self.pitch_to_str(1), self.is_playing[0], self.is_playing[1],
                       self.is_on_headphone[0], self.is_on_headphone[1], self.volume[0], self.volume[1]]
        except Exception as e:
            logger.error(e)
        else:
            self.tx_update_gui.send(tx_data)

    def set_new_track(self, future):
        result = future.result()
        path = result[0]
        channel = result[1]
        self.is_loading[channel] = False
        if self.shared_table_p is None:
            logger.error("no table")
            return
        try:
            self.track[channel] = Track(title=str(path.split("/")[-1:][0].split(".")[:-1][0]), bpm="120 bpm", path=path)
        except Exception as e:
            logger.error(e)
            return
        self.phasor[channel].reset()
        self.phasor[channel].freq = 0
        self.pointer[channel].table = self.shared_table_p[channel]
        self.tx_new_track.send([channel, self.track[channel]])

    # def get_bpm  # TODO impl fn get_bpm

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

    def set_position(self, position: float, channel: int) -> None:  # TODO not using this function yet, maybe for loop
        self.phasor[channel].reset()
        self.phasor[channel].phase = position

    def set_line_volume(self, value: float, channel: int) -> None:
        self.mixer.setAmp(channel, 0, value)

    def set_main_volume(self, value: float) -> None:
        self.mainVolume.setAmp(0, 0, value)

    def jump(self, diff: float, channel: int) -> None:
        if 0 <= self.phasor[channel].get() % 1 + diff <= 1:  # modulo for replay loop
            self.phasor[channel].phase += diff
        else:
            logger.info("tried to jump out of bounds")

    # TODO universal system of input values maybe between -1 and 1
    def set_eq(self, equalizer: EQ, value: float) -> None:
        if value > 0:
            value /= 10  # weaker increasing than lowering
        equalizer.boost = value * 40  # max lowering 40dB

    def pos_to_str(self, channel: int) -> str:
        sec, dur = (self.phasor[channel].get() * self.get_dur(channel),
                    self.get_dur(channel))
        return "{}:{}/{}:{}".format(str(int(sec / 60)), str(int(sec) % 60).zfill(2), str(int(dur / 60)),
                                    str(int(dur) % 60).zfill(2))

    def pitch_to_str(self, channel: int) -> str:
        return "{0}{1:.1f}%".format(("+" if self.pitch[channel] >= 1 else ""), (self.pitch[channel] - 1) * 100)

    def get_dur(self, channel: int) -> float:
        return self.shared_table_p[channel].getSize() / 44100
