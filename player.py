# CLEANED UP

from pyo import *
import logging
import multiprocessing
import sys
from kivy.clock import Clock
from multiprocessing.connection import Connection
# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


class Player:  # TODO shared memory?
    def __init__(self, tx: Connection) -> None:
        super(Player, self).__init__()
        self.tx = tx

        # Properties
        self.server = Server()
        self.server.setInOutDevice(8)
        self.server.boot()
        self.server.start()
        self.table = [SndTable(), SndTable()]
        self.title = ["", ""]
        self.is_playing = [False, False]
        self.is_on_headphone = [False, False]
        self.refresh_snd = [False, False]

        # Audio Modules
        self.phasor = [Phasor(freq=0), Phasor(freq=0)]
        self.pointer = [Pointer(table=self.table[0], index=self.phasor[0], mul=0.3),
                        Pointer(table=self.table[1], index=self.phasor[1], mul=0.3)]  # TODO why mul != 1?
        self.pitch = [1, 1]
        self.lowEq = [EQ(input=self.pointer[0], boost=1, freq=125, q=1, type=1),  # TODO good choice for frequencies?
                      EQ(input=self.pointer[1], boost=1, freq=125, q=1, type=1)]
        self.midEq = [EQ(input=self.lowEq[0], boost=1, freq=1200, q=0.5, type=0),
                      EQ(input=self.lowEq[1], boost=1, freq=1200, q=0.5, type=0)]
        self.highEq = [EQ(input=self.midEq[0], boost=1, freq=8000, q=1, type=2),
                       EQ(input=self.midEq[1], boost=1, freq=8000, q=1, type=2)]
        self.mixer = Mixer(outs=1, chnls=2)
        self.mixer.addInput(0, self.highEq[0])
        self.mixer.addInput(1, self.highEq[1])
        self.mixer.setAmp(0, 0, 1)  # TODO controlling volume
        self.mixer.setAmp(1, 0, 1)
        self.mainVolume = Mixer(outs=1, chnls=2)
        self.mainVolume.addInput(0, self.mixer[0])
        self.mainVolume.setAmp(0, 0, 1)
        self.mainVolume.out(1)

        Clock.schedule_interval(self.handler_send, 0.1)

    def handler_send(self, dt):
        tx_data = [self.phasor[0].phase, self.phasor[1].phase, self.pos_to_str(0), self.pos_to_str(1),
                   self.pitch_to_str(0), self.pitch_to_str(1), self.is_playing[0], self.is_playing[1],
                   self.is_on_headphone[0], self.is_on_headphone[1]]
        self.tx.send(tx_data)

    def start_stop(self, channel: int) -> None:
        if self.is_playing[channel]:
            self.phasor[channel].freq = 0
            self.is_playing[channel] = False
        else:
            self.phasor[channel].freq = self.table[channel].getRate() * self.pitch[channel]
            self.is_playing[channel] = True
            logger.info("started playback")

    def set_pitch(self, value: int, channel: int) -> None:
        self.pitch[channel] = value
        if self.table[channel] is not None:
            self.phasor[channel].freq = value * self.table[channel].getRate()
        else:
            logger.info("no track loaded")

    def set_position(self, position: float, channel: int) -> None:  # TODO not using this function yet
        self.phasor[channel].reset()
        self.phasor[channel].phase = position

    def jump_position(self, diff: float, channel: int) -> None:
        if 0 <= self.phasor[channel].phase + diff <= 1:
            self.phasor[channel].phase += diff
        else:
            logger.info("tried to jump out of bounds")

    # TODO universal system of input values maybe between -1 and 1
    def set_eq(self, equalizer: EQ, value: float) -> None:
        if value > 0:
            value /= 10  # weaker increasing than lowering
        equalizer.boost = value * 40  # max lowering 40dB

    def pos_to_str(self, channel: int):
        sec, dur = (self.phasor[channel].phase * self.table[channel].getDur(), self.table[channel].getDur())
        return "{}:{}/{}:{}".format(str(int(sec/60)), str(sec%60).zfill(2), str(int(dur/60)), str(dur%60).zfill(2))

    def pitch_to_str(self, channel: int):
        return "{}{}%".format(("+" if self.pitch[channel] else ""), self.pitch[channel] * 100)




