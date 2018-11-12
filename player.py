# CLEANED UP

from pyo import *
import logging
import multiprocessing

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Player(multiprocessing.Process):
    def __init__(self) -> None:
        super(Player, self).__init__()
        # Properties
        self.server = Server()
        self.server.setInOutDevice(8)
        self.server.boot()
        self.server.start()
        self.table = [SndTable(), SndTable()]
        self.title = ["", ""]
        self.isPlaying = [False, False]
        self.refresh_snd = [False, False]

        # Audio Modules
        self.phasor = [Phasor(freq=0), Phasor(freq=0)]
        self.pointer = [Pointer(table=self.table[0], index=self.phasor[0], mul=0.3),
                        Pointer(table=self.table[1], index=self.phasor[1], mul=0.3)]  # TODO check # mul != 1n?
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

    def start_stop(self, channel: int) -> None:
        if self.isPlaying[channel]:
            self.phasor[channel].freq = 0
            self.isPlaying[channel] = False
        else:
            self.phasor[channel].freq = self.table[channel].getRate() * self.pitch[channel]
            self.isPlaying[channel] = True

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
