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
import config
from lib import *
import cache

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
        self.server.setInOutDevice(config.audio_device)
        self.server.boot()
        self.server.start()
        self.track = [Track(), Track()]
        #self.track_info = [TrackInfo(), TrackInfo()]
        self.is_playing = [False, False]
        self.is_on_headphone = [False, False]
        self.is_loading = [False, False]
        self.refresh_snd = [False, False]
        self.pitch = [1, 1]
        self.volume = [0, 0]
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)

        # Audio Modules
        self.phasor = [Phasor(freq=0), Phasor(freq=0)]  # TODO prevent from looping, ask muvlon
        self.pointer = [Pointer(table=self.shared_table_p[0], index=self.phasor[0], mul=1),
                        Pointer(table=self.shared_table_p[1], index=self.phasor[1], mul=1)]
        self.lowEq = [EQ(input=self.pointer[0], boost=1, freq=config.frequency_low, q=1, type=1),  # TODO good choice for frequencies?
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
        Clock.schedule_interval(self.handler_cache, config.chunk_size/4.0)
    
        # Cache
        self.cache = Cache()
        self.begin_offset = [0, 0]
   
    # CHECKED
    def handler_cache(self, dt):
        self.check_cache(0)
        self.check_cache(1)

    # TODO waht if ne track 
    # TODO what if new track shorter than cache size 
    
    def check_cache(self, channel: int) -> None:
        chunk_diff = lib.time_to_chunks(get_pos_rel(channel) - lib.chunks_to_time(config.cache_size)/2.0)
        if chunk_diff is 0:
            return 
        
        elif chunk_diff < 0:
            if self.begin_offset(channel) + chunk_diff >=0:
                new_begin = self.begin_offset(channel) + chunk_diff
                self.cache.insert(path=self.track[channel].path, channel=channel, src_begin=new_begin, size=config.cache_size, back=False)
            else :
                logger.warning("already at start")
                return
        elif chunk_diff > 0:
            if self.begin_offset(channel) + config.cache_size + chunk_diff <= lib.time_to_chunks(self.get_dur()):
                new_begin = self.begin_offset(channel) + chunk_diff
                self.cache.insert(path=self.track[channel].path, channel=channel, src_begin=new_begin, size=config.cache_size, back=True)
            else:
                else :
                logger.warning("already at end")
                return
    
    # CHECKED
    def get_volume0(self, *args):
        if len(args) != 1:
            logger.error("no args")
            return
        self.volume[0] = args[0]

    # CHECKED
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
                #if self.is_loading[args[1]]:
                #    logger.info("is already loading")
                #    return
                elif self.is_playing[args[1]]:
                    logger.info("is playing")
                    return
                info = float(ffmpeg.probe(args[0])["format"]["duration"]) * config.sample_rate
                self.shared_table_p[args[1]] = SharedTable(["/sharedl{}".format(args[1]), "/sharedr{}".format(args[1])], #TODO 
                                                           True, int(info))
                future = self.executor.submit(track_loading.load, args[0], args[1], self.tx_wav_data)
                self.is_loading[args[1]] = True
                future.add_done_callback(self.set_new_track)

    def refresh_gui(self, dt):
        try:
            tx_data = [self.phasor[0].get(), self.phasor[1].get(), self.pos_to_str(self.get_pos_abs(0), lib.get_dur(self.track[0].path)), self.pos_to_str(self.get_pos_abs(1), lib.get_dur(self.track[1].path),
                       pitch_to_str(self.pitch[0]), pitch_to_str(self.pitch[0]), self.is_playing[0], self.is_playing[1],
                       self.is_on_headphone[0], self.is_on_headphone[1], self.volume[0], self.volume[1]]
        except Exception as e:
            logger.error(e)
        else:
            self.tx_update_gui.send(tx_data)


    def set_new_track(self, future):
        result = future.result()
        path = future.result()[0]
        channel = future.result()[1]
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

    def set_line_volume(self, value: float, channel: int) -> None:
        self.mixer.setAmp(channel, 0, value)

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
        return self.phasor[channel].get() * config.cache_size + lib.chunks_to_time(self.begin_offset) 
        
    # CHECKED
    def get_pos_rel(self, channel: int) -> float:
        return self.phasor[channel].get() * config.cache_size