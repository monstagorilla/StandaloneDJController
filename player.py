from pyo import *
import logging
import multiprocessing
import sys
from kivy.clock import Clock
from multiprocessing.connection import Connection
import concurrent.futures
from gui_classes import Track
import ffmpeg
import config
from lib import *

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(config.logging_level)
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
        self.server.setInOutDevice(config.audio_device)
        self.server.boot()
        self.server.start()
        self.track = [Track(), Track()]
        #self.track_info = [TrackInfo(), TrackInfo()]
        self.is_playing = [False, False]
        self.is_on_headphone = [False, False]
        #self.refresh_snd = [False, False]
        self.pitch = [1, 1]
        self.volume = [0, 0]

        # Cache
        self.cache = Cache(self)
        self.begin_offset = [0, 0]

        # Audio Modules
        self.phasor = [Phasor(freq=0), Phasor(freq=0)]  # TODO prevent from looping
        self.pointer = [Pointer(table=self.cache.shared_table[0], index=self.phasor[0], mul=1),
                        Pointer(table=self.cache.shared_table[1], index=self.phasor[1], mul=1)]
        self.lowEq = [EQ(input=self.pointer[0], boost=1, freq=config.frequency_low, q=1, type=1),
                      EQ(input=self.pointer[1], boost=1, freq=config.frequency_low, q=1, type=1)]
        self.midEq = [EQ(input=self.lowEq[0], boost=1, freq=config.frequency_mid, q=0.5, type=0),
                      EQ(input=self.lowEq[1], boost=1, freq=config.frequency_mid, q=0.5, type=0)]
        self.highEq = [EQ(input=self.midEq[0], boost=1, freq=config.frequency_high, q=1, type=2),
                       EQ(input=self.midEq[1], boost=1, freq=config.frequency_high, q=1, type=2)]
        self.mixer = Mixer(outs=1, chnls=2)
        self.mixer.addInput(0, self.highEq[0])
        self.mixer.addInput(1, self.highEq[1])
        self.mixer.setAmp(0, 0, 0.5)
        self.mixer.setAmp(1, 0, 0.5)
        self.mainVolume = Mixer(outs=1, chnls=2)
        self.mainVolume.addInput(0, self.mixer[0])
        self.mainVolume.setAmp(0, 0, 1)
        self.mainVolume.out(1)
        self.volume_meter_0 = PeakAmp(self.highEq[0], function=self.get_volume0)
        self.volume_meter_1 = PeakAmp(self.highEq[1], function=self.get_volume1)

        # clock scheduling
        Clock.schedule_interval(self.refresh_gui, 0.001)
        Clock.schedule_interval(self.handler_player_fn, 0.001)
        #Clock.schedule_interval(self.handler_cache, config.chunk_size/4.0)
        Clock.schedule_interval(self.handler_cache, 1)

    # CHECKED
    def handler_cache(self, dt):
        self.check_cache(0)
        self.check_cache(1)
        a = self.get_pos_abs(0)  # DEBUG

    # TODO what if ne track
    # TODO what if new track shorter than cache size

    def check_cache(self, channel: int) -> None:
        chunk_diff = time_to_chunks(self.get_pos_rel(channel) - chunks_to_time(config.cache_size)/2.0)
        if chunk_diff is 0:
            return
        elif chunk_diff < 0:  # player plays before mid of cache
            if self.begin_offset[channel] + chunk_diff >= 0:  # it is possible to load chunks before actual cache
                src_begin = self.begin_offset[channel] + chunk_diff
                self.cache.insert(path=self.track[channel].path, channel=channel, src_begin=src_begin,
                                  size=abs(chunk_diff), back=False)
            else:
                logger.info("already at start")
                return
        elif chunk_diff > 0:  # player plays after mid of cache
            if self.begin_offset[channel] + config.cache_size  + chunk_diff <= time_to_chunks(get_dur(self.track[channel].path)) + 1 :  # it is possible to load chunks after actual cache, +1 because of floor rounding in get_dur()
                src_begin = self.begin_offset[channel] + (config.cache_size - 1) + chunk_diff  # -1 because of position not size
                if self.cache.is_loading[channel]:
                    return
                else:
                    self.cache.insert(path=self.track[channel].path, channel=channel, src_begin=src_begin, size=abs(chunk_diff), back=True)
            else:
                logger.info("already at end")
                return

    # CHECKED
    def get_volume0(self, *args):  # TODO: Documentation
        if len(args) != 1:
            #logger.error("no args")
            return
        self.volume[0] = args[0]

    # CHECKED
    def get_volume1(self, *args):
        if len(args) != 1:
            #logger.error("no args")
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
                if self.cache.is_loading[args[1]]:
                    logger.info("is already loading")
                    return
                elif self.is_playing[args[1]]:
                    logger.info("is playing")
                    return
                self.cache.insert(path=args[0], channel=args[1], src_begin=0, size=config.cache_size, is_new_track=True)

    def refresh_gui(self, dt):
        if self.track[0].path == "" or self.track[1].path == "":
            return
        try:
            tx_data = [self.phasor[0].get(), self.phasor[1].get(), pos_to_str(self.get_pos_abs(0), get_dur(self.track[0].path)),
                       pos_to_str(self.get_pos_abs(1), get_dur(self.track[1].path)),
                       pitch_to_str(self.pitch[0]), pitch_to_str(self.pitch[0]), self.is_playing[0], self.is_playing[1],
                       self.is_on_headphone[0], self.is_on_headphone[1], self.volume[0], self.volume[1]]
        except Exception as e:
            logger.error(e)
        else:
            self.tx_update_gui.send(tx_data)

    def done_cache_update(self, future) -> None:
        result = future.result()
        channel = result[0]
        offset_diff = result[1]
        self.begin_offset[channel] += int(offset_diff)
        logger.debug("OFFSET_DIFF: " + str(offset_diff))
        logger.debug("NEW_OFFSET: " + str(self.begin_offset[channel]))
        self.cache.is_loading[channel] = False

    def done_new_track(self, future) -> None:
        result = future.result()

        assert len(result) == 3

        channel = result[0]
        offset_diff = result[1]
        path = result[2]

        if self.cache.shared_table[channel] is None:
            logger.error("no table")
            return
        try:
            self.track[channel] = Track(title=str(path.split("/")[-1:][0].split(".")[:-1][0]), bpm="120 bpm", path=path)
        except Exception as e:
            logger.error(e)
            return
        self.phasor[channel].reset()
        self.phasor[channel].freq = 0
        self.tx_new_track.send([channel, self.track[channel]])
        self.cache.is_loading[channel] = False


    # def get_bpm  TODO impl fn get_bpm

    # CHECKED
    def start_stop(self, channel: int) -> None:
        if self.is_playing[channel]:
            self.phasor[channel].freq = 0
            self.is_playing[channel] = False
            logger.info("stopped playback on channel {}".format(channel))
        else:
            if not self.cache.shared_table[channel]: # TODO never happens because init
                logger.error("no track loaded")
                return
            self.phasor[channel].freq = self.cache.shared_table[channel].getRate() * self.pitch[channel]
            self.is_playing[channel] = True
            logger.info("started playback on channel {}".format(channel))

    # CHECKED
    def set_pitch(self, value: int, channel: int) -> None:
        self.pitch[channel] = value
        if self.cache.shared_table[channel] is not None:
            self.phasor[channel].freq = value * self.cache.shared_table[channel].getRate()
        else:
            logger.info("no track loaded")

    def set_position(self, position: float, channel: int) -> None:  # TODO not using this function yet, maybe for loop
        self.phasor[channel].reset()
        self.phasor[channel].phase = position

    # CHECKED
    def set_line_volume(self, value: float, channel: int) -> None:
        self.mixer.setAmp(channel, 0, value)

    # CHECKED
    def set_main_volume(self, value: float) -> None:
        self.mainVolume.setAmp(0, 0, value)

    # CHECKED
    # TODO jump is relative to cache size
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

    # CHECKED
    def get_pos_abs(self, channel: int) -> float:
        logger.info("abs_time: " + str(self.get_pos_rel(channel) + chunks_to_time(self.begin_offset[channel])))
        return self.get_pos_rel(channel) + chunks_to_time(self.begin_offset[channel])

    # CHECKED
    def get_pos_rel(self, channel: int) -> float:
        diff = self.phasor[channel].get() - chunks_to_time(self.begin_offset[channel] % config.cache_size) / chunks_to_time(config.cache_size)
        if diff < 0:
            result = (1 + diff) * chunks_to_time(config.cache_size)
        else:
            result = diff * chunks_to_time(config.cache_size)
        return result

from cache import Cache  # TODO: different solution for dependency cycle
