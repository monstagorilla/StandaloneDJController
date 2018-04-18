from pyo import *
import wx
import time 

class Player:
    def __init__(self):
        self.server = Server()
        self.server.setInOutDevice(7)
        self.server.boot()
        self.table = [SndTable(), SndTable()]
        self.mono_table = [SndTable(), SndTable()]
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
        self.mainVolume = Mixer(outs = 1, chnls = 2)
        self.mainVolume.addInput(0, self.mixer[0])
        self.mainVolume.setAmp(0, 0, 1)
        self.mainVolume.out(1)
        self.lowEq[0].ctrl(title = "low0")
        self.lowEq[1].ctrl(title = "low1")
        self.midEq[0].ctrl(title = "mid0")
        self.midEq[1].ctrl(title = "mid1")
        self.highEq[0].ctrl(title = "high0")
        self.highEq[1].ctrl(title = "high1")

    def load_track(self, path, channel):
        self.table[channel] = SndTable(path)
        self.mono_table[channel] = SndTable(path = path, chnl = 0)
        self.phasor[channel].freq = self.table[channel].getRate()
        self.pointer[channel].table = self.table[channel]

    def start_stop(self, channel):
        if self.isPlaying[channel]:
            self.phasor[channel].freq = 0
            self.isPlaying[channel] = False
        else:
            self.phasor[channel].freq = self.table[channel].getRate() * self.pitch[channel]
            self.isPlaying[channel] = True

    def set_pitch(self, value, channel):
        self.pitch[channel] = value 
        self.phasor[channel].freq = value * self.table[channel].getRate()

    def set_position(self, position, channel):
        self.phasor[channel].reset()
        self.phasor[channel].phase = position

    def jump_position(self, diff, channel):
        if 0 <= (self.phasor[channel].phase + diff) and (self.phasor[channel].phase + diff) <= 1:
            self.phasor[channel].phase += diff
        else:
            print("jump not in range")

    def set_eq(self, equalizer, value):
        if value > 0:
            value /= 10 #weaker increasing than lowering
        equalizer.boost = value * 40 #max lowering 40dB

class MyFrame(wx.Frame):
    def __init__(self, player):
        wx.Frame.__init__(self, None, style = wx.NO_BORDER | wx.CAPTION)
        self.box_sizer_v = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.box_sizer_v)

        self.is_running = True
        self.new_input = ""
        self.player = player
        self.snd_view = [PyoGuiSndView(parent = self), PyoGuiSndView(parent = self)]
        self.snd_view[0].setTable(player.mono_table[0])
        self.snd_view[1].setTable(player.mono_table[1])
        self.box_sizer_v.Add(self.snd_view[0], 0, wx.ALL)
        self.box_sizer_v.Add(self.snd_view[1], 0, wx.ALL)
        self.box_sizer_v.Fit(self)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(10)
   
    def update(self, event):
        self.snd_view[0].setSelection(0, self.player.phasor[0].get())
        self.snd_view[1].setSelection(0, self.player.phasor[1].get())
        print(self.player.phasor[0].get())
        '''
        while self.is_running:
            if self.new_input == "s0":
                p.start_stop(0)
            elif self.new_input == "s1":
                p.start_stop(1)
            elif self.new_input == "pitch0":
                p.set_pitch(float(input("pitch channel 0 between 0 and 1")), 0)
            elif self.new_input == "pitch1":
                p.set_pitch(float(input("pitch channel 1 between 0 and 1")), 1)
            elif self.new_input == "pos0":
                p.set_position(float(input("position channel 0 between 0 and 1")), 0)
            elif self.new_input == "pos1":
                p.set_position(float(input("position channel 1 between 0 and 1")), 1)
            elif self.new_input == "jump0":
                p.jump_position(float(input("jump diff channel 0 between 0 and 1")), 0)
            elif self.new_input == "jump1":
                p.jump_position(float(input("jump diff channel 1 between 0 and 1")), 1)    
            elif self.new_input == "eq0":
                which_input = input("which eq?")
                if which_input == "low":
                    p.set_eq(p.lowEq[0], float(input("low boost channel 0 between 0 and 1")))
                elif which_input == "mid":
                    p.set_eq(p.midEq[0], float(input("mid boost channel 0 between 0 and 1")))
                elif which_input == "high":
                    p.set_eq(p.highEq[0], float(input("high boost channel 0 between 0 and 1")))
                else: 
                    print("invalid eq")    
            elif self.new_input == "eq1":
                which_input = input("which eq for channel 1?")
                if which_input == "low":
                    p.set_eq(p.lowEq[1], float(input("low boost channel 1 between 0 and 1")))
                elif which_input == "mid":
                    p.set_eq(p.midEq[1], float(input("mid boost channel 1 between 0 and 1")))
                elif which_input == "high":
                    p.set_eq(p.highEq[1], float(input("high boost channel 1 between 0 and 1")))
                else: 
                    print("invalid eq")
            elif self.new_input == "quit":
                self.is_running = False
            else:
                print("invalid input")
'''
p = Player()
p.load_track('test.wav', 0)
p.load_track('test2.wav',1)
p.start_stop(0)
p.start_stop(1)
p.server.start()
app = wx.App()
frame = MyFrame(p).Show()
app.MainLoop()
