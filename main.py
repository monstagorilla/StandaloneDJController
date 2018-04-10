from pyo import *
import wx
class Player:
    def __init__(self):
        self.server = Server()
        self.server.setInOutDevice(7)
        self.server.boot()
        self.table = SndTable()
        self.isPlaying = False
        self.phasor = Phasor(freq = 0)
        self.pointer = Pointer(table = self.table, index = self.phasor, mul = 0.3)
        #self.volume = 1
        self.pitch = 1
        self.lowEq = EQ(input = self.pointer, boost = 1, freq = 125, q = 1, type = 1)
        self.midEq = EQ(input = self.lowEq, boost = 1, freq = 1200, q = 0.5, type = 0) 
        self.highEq = EQ(input = self.midEq, boost = 1, freq = 8000, q = 1, type =2).out()
        self.lowEq.ctrl(title = "low")
        self.midEq.ctrl(title = "mid")
        self.highEq.ctrl(title = "high")

    def load_track(self, path):
        self.table = SndTable(path)
        self.phasor.freq = self.table.getRate()
        self.pointer.table = self.table

    def start_stop(self):
        if self.isPlaying:
            self.phasor.freq = 0
            self.isPlaying = False
        else:
            self.phasor.freq = self.table.getRate() * self.pitch
            self.isPlaying = True

    def setPitch(self, value):
        self.pitch = value
        self.phasor.freq = value * self.table.getRate()

    def setPostion(self, position):
        self.phasor.phase = postion

    def jumpPosition(self, diff):
        if 0 <= self.phasor.phase + diff <= 1:
            self.phasor.phase += diff

    def setEq(equalizer, value):
        if value > 0:
            value /= 10 #weaker increasing than lowering
        equalizer.boost = value * 40 #max lowering 40dB

p = Player()
p.load_track('/home/monstagorilla/Documents/Coding/StandaloneDJController/test.wav')
p.start_stop()
app = wx.App()
frame = wx.Frame(None, style= wx.NO_BORDER | wx.CAPTION)
frame.Show()
snd_view = PyoGuiSndView(parent = frame)
snd_view.setTable(p.table)

app.MainLoop()
#p.server.gui()
