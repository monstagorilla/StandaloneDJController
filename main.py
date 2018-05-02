from pyo import *
import wx
import time 

#GUI-TODOs: handler fertig schreiben, unterschiedliche cmd level handlen, lbls für song stats, track auswählen


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
        if not self.isPlaying[channel]:
            return
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
        self.cmd_state = ""
        self.cmd_chnl = ""
        self.player = player
        self.snd_view = [PyoGuiSndView(parent = self), PyoGuiSndView(parent = self)]
        self.snd_view[0].setTable(player.mono_table[0])
        self.snd_view[1].setTable(player.mono_table[1])
        self.cmd = wx.TextCtrl(parent = self, style = wx.TE_PROCESS_ENTER)
        self.text = wx.TextCtrl(parent = self)
        self.timer = wx.Timer(self)
        self.box_sizer_v.Add(self.cmd, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 5)
        self.box_sizer_v.Add(self.text, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 5)
        self.box_sizer_v.Add(self.snd_view[0], 0, wx.ALL)
        self.box_sizer_v.Add(self.snd_view[1], 0, wx.ALL)
        self.box_sizer_v.Fit(self)
        self.timer.Start(10)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.cmd.Bind(wx.EVT_TEXT_ENTER, self.new_cmd)

    def new_cmd(self, event):
        self.new_input = self.cmd.GetLineText(0)
        if self.cmd_state == "":
            if self.new_input == "s0":
                self.player.start_stop(0)
                self.print_msg("")
            elif self.new_input == "s1":
                self.player.start_stop(1) 
                self.print_msg("")
            elif self.new_input == "pitch0":
                self.print_msg("pitch channel 0 between 0 and 1")
                self.cmd_state = "pitch"
                self.cmd_chnl = 0
            elif self.new_input == "pitch1":
                self.print_msg("pitch channel 1 between 0 and 1")
                self.cmd_state = "pitch"
                self.cmd_chnl = 1
            elif self.new_input == "pos0":
                self.print_msg("position channel 0 between 0 and 1")
                self.cmd_state = "pos"
                self.cmd_chnl = 0
            elif self.new_input == "pos1":
                self.print_msg("position channel 1 between 0 and 1")
                self.cmd_state = "pos"
                self.cmd_chnl = 1
            elif self.new_input == "jump0":
                self.print_msg("jump diff channel 0 between 0 and 1")
                self.cmd_state = "jump"
                self.cmd_chnl = 0
            elif self.new_input == "jump1":
                self.print_msg("jump diff channel 1 between 0 and 1")
                self.cmd_state = "jump"
                self.cmd_chnl = 1
            elif self.new_input == "low0":
                self.print_msg("low boost channel 0 between 0 and 1")
                self.cmd_state = "low"
                self.cmd_chnl = 0
            elif self.new_input == "low1":
                self.print_msg("low boost channel 1 between 0 and 1")
                self.cmd_state = "low"
                self.cmd_chnl = 1
            elif self.new_input == "mid0":
                self.print_msg("low boost channel 0 between 0 and 1")
                self.cmd_state = "mid"
                self.cmd_chnl = 0
            elif self.new_input == "mid1":
                self.print_msg("mid boost channel 1 between 0 and 1")
                self.cmd_state = "mid"
                self.cmd_chnl = 1
            elif self.new_input == "high0":
                self.print_msg("high boost channel 0 between 0 and 1")
                self.cmd_state = "high"
                self.cmd_chnl = 0
            elif self.new_input == "high1":
                self.print_msg("high boost channel 1 between 0 and 1")
                self.cmd_state = "high"
                self.cmd_chnl = 1
            else:
                self.cmd_state = ""
                self.print_msg("invalid input")
        else:
            try: 
                if self.cmd_state == "pitch":
                    self.player.set_pitch(float(self.new_input), self.cmd_chnl)
                elif self.cmd_state == "pos":
                    self.player.set_position(float(self.new_input), self.cmd_chnl)
                elif self.cmd_state == "jump":
                    self.player.jump_position(float(self.new_input), self.cmd_chnl)
                elif self.cmd_state == "low":
                    self.player.set_eq(self.player.lowEq[self.cmd_chnl], float(self.new_input))
                elif self.cmd_state == "mid":
                    self.player.set_eq(self.player.midEq[self.cmd_chnl], float(self.new_input))
                elif self.cmd_state == "high":
                    self.player.set_eq(self.player.highEq[self.cmd_chnl], float(self.new_input))
                elif self.cmd_state == "quit":
                    print("quit")
            except:
                self.print_msg("invalid input!!!!")
            self.cmd_state = ""
            self.print_msg("")
        
    def update(self, event):
        self.snd_view[0].setSelection(0, self.player.phasor[0].get())
        self.snd_view[1].setSelection(0, self.player.phasor[1].get())
    
    def print_msg(self, text):
        self.text.Clear()
        self.text.AppendText(text)
        self.cmd.Clear()

p = Player()
p.load_track('test.wav', 0)
p.load_track('test2.wav',1)
p.start_stop(0)
p.start_stop(1)
p.server.start()
app = wx.App()
frame = MyFrame(p).Show()
app.MainLoop()
