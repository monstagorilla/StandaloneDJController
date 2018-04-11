from pyo import *
import wx
class Player:
    def __init__(self):
        self.server = Server()
        self.server.setInOutDevice(7)
        self.server.boot()
        self.table = [SndTable(), SndTable()]
        self.isPlaying = [False, False]
        self.phasor = [Phasor(freq = 0), Phasor(freq = 0)]
        self.pointer = [Pointer(table = self.table[0], index = self.phasor[0], mul = 0.3),
                        Pointer(table = self.table[1], index = self.phasor[1], mul = 0.3)]
        self.pitch = [1, 1]
        self.lowEq = [EQ(input = self.pointer[0], boost = 1, freq = 125, q = 1, type = 1),
                      EQ(input = self.pointer[1], boost = 1, freq = 125, q = 1, type = 1)]
        self.midEq = [EQ(input = self.lowEq[0], boost = 1, freq = 1200, q = 0.5, type = 0),
                      EQ(input = self.lowEq[1], boost = 1, freq = 1200, q = 0.5, type = 0)]
        self.highEq = [EQ(input = self.midEq[0], boost = 1, freq = 8000, q = 1, type =2),
                       EQ(input = self.midEq[1], boost = 1, freq = 8000, q = 1, type =2)]
        self.mixer = Mixer(outs = 1, chnls = 2)
        self.mixer.addInput(0, self.highEq[0])
        self.mixer.addInput(1, self.highEq[1])
 
        self.mixer.setAmp(0, 0, 1)
        self.mixer.setAmp(1, 0, 1)
        
        self.mainVolume = Mixer(outs = 1, chnls = 1)
        self.mainVolume.addInput(0, self.mixer[0])
        self.mainVolume.setAmp(0, 0, 1)
        self.mainVolume.out()
        self.lowEq[0].ctrl(title = "low0")
        self.lowEq[1].ctrl(title = "low1")
        self.midEq[0].ctrl(title = "mid0")
        self.midEq[1].ctrl(title = "mid1")
        self.highEq[0].ctrl(title = "high0")
        self.highEq[1].ctrl(title = "high1")

    def load_track(self, path, channel):
        self.table[channel] = SndTable(path)
        self.phasor[channel].freq = self.table[channel].getRate()
        self.pointer[channel].table = self.table[channel]

    def start_stop(self, channel):
        if self.isPlaying[channel]:
            self.phasor[channel].freq = 0
            self.isPlaying[channel] = False
        else:
            self.phasor[channel].freq = self.table[channel].getRate() * self.pitch[channel]
            self.isPlaying[channel] = True

    def setPitch(self, value, channel):
        self.pitch[channel] = value
        self.phasor[channel].freq = value * self.table[channel].getRate()

    def setPostion(self, position, channel):
        self.phasor[channel].phase = postion

    def jumpPosition(self, diff, channel):
        if 0 <= self.phasor[channel].phase + diff <= 1:
            self.phasor[channel].phase += diff

    def setEq(equalizer, value):
        if value > 0:
            value /= 10 #weaker increasing than lowering
        equalizer.boost = value * 40 #max lowering 40dB

p = Player()
p.load_track('test.wav', 0)
p.load_track('test2.wav',1)

p.start_stop(0)
p.start_stop(1)
#app = wx.App()
#frame = wx.Frame(None, style= wx.NO_BORDER | wx.CAPTION)
#frame.Show()
#snd_view = PyoGuiSndView(parent = frame)
#snd_view.setTable(p.table)

#app.MainLoop()
p.server.gui()
