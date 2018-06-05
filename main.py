#!/usr/bin/env python3

from pyo import *
import wx
import time 
import shutil
import subprocess
import threading
import multiprocessing 
#GUI-TODOs: style of textctrls
#possible issues: simultanious track loading, displa track name
class Player():
    def __init__(self):
        self.server = Server()
        self.server.setInOutDevice(7)
        self.server.boot()
        self.table = [SndTable(), SndTable()]
        self.mono_table = [SndTable(chnl = 0), SndTable(chnl = 0)]
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
        self.refresh_snd = [False, False]

    def decode_mp3(self, i_path, o_path):
        return subprocess.Popen(["ffmpeg", "-i", i_path, o_path]) 

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

class Lib:
    def decode_mp3(self, i_path, o_path):
        return subprocess.Popen(["ffmpeg", "-i", i_path, o_path]) 
    
class TrackLoader(threading.Thread):
    def __init__(self, player, path, channel):
        threading.Thread.__init__(self)
        self.player = player
        self.path = path
        self.channel = channel
        #thread = threading.Thread(target = self.run, args = ())
        #thread.daemon = True
        #thread.start()

    def run(self): 
        info = sndinfo(self.path)
        dur = info[1]
        #print("duration: " + str(dur))
        cur_time = 0.0
        step = 1.0
        if step <= dur:
            self.player.table[self.channel] = SndTable()
            #self.player.tablje[self.channel].setSound(self.path, 1, step)
            #self.player.mono_table[self.channel].setSound(self.path, 0, step)
        else:
            print("track too short") #TODO implement better solution
        cur_time = step
        flag = True
        while flag:
            if cur_time + step > dur:
                step = dur - cur_time
                flag = False
            #stop_time = cur
            #print("lololo")

            stop_time = cur_time + step
            try:
                self.player.table[self.channel].append(self.path, 0, cur_time, stop_time)
                #self.player.mono_table[self.channel].append(self.path, 0, cur_time, stop_time)
            except TypeError as te:
                print("arguments: {}, {}, {}".format(type(self.path), type(cur_time), type(stop_time)))
                print(te)
            cur_time += step
            time.sleep(0.000001)

        self.player.pointer[self.channel].table = self.player.table[self.channel]
        self.player.phasor[self.channel].reset()
        self.player.phasor[self.channel].freq = 0
        self.player.refresh_snd[self.channel] = True

class BrowserFrame(wx.Frame):
    def __init__(self, player):
        wx.Frame.__init__(self, None,  style = wx.NO_BORDER | wx.CAPTION)
        self.player = player
        self.path_root = "/home/monstagorilla/Music"
        self.path = self.path_root
        self.path_temp = self.path_root + "/temp"
        if os.path.isdir(self.path_temp):
            self.clear_temp()
        else:
            os.mkdir(self.path_temp)
        self.dir_list = []
        self.track_list = []
        self.index = 0
        self.dir_lvl = 0
         
        self.decode_is_running = False
        self.decode_obj = None
        
        self.new_track = ["", 0, ""] #[path, chnl, codec] 
        
        self.timer = wx.Timer(self)
        self.timer.Start(100)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)

        self.box_sizer_v = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.box_sizer_v)

        self.list_ctrl = wx.ListCtrl(parent = self, size = (400, 300), style = wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "Title", width = 200)
        self.path_label = wx.TextCtrl(parent = self, size = (400, -1), style = wx.TE_READONLY, value = self.path)
        self.refresh_list_view()

        self.box_sizer_v.Add(self.path_label, 0, wx.ALL)
        self.box_sizer_v.Add(self.list_ctrl, 0, wx.ALL)
        self.box_sizer_v.Fit(self)
        
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_pressed)
        self.list_ctrl.SetFocus()
    
    def clear_temp(self):
        for the_file in os.listdir(self.path_temp):
            file_path = os.path.join(self.path_temp, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): 
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)

    def update(self, event):
        if self.decode_is_running:
            if self.decode_is_running == True and self.decode_obj.poll() != None: #TODO: return code check
                #self.player.load_track(self.new_track[0], self.new_track[1])
                t = TrackLoader(self.player, self.new_track[0], self.new_track[1])
                t.start()
                self.player.refresh_snd[self.new_track[1]] = True
                #self.clear_temp()
                self.decode_is_running = False
    
    def refresh_list_view (self):
        self.index = 0
        self.list_ctrl.DeleteAllItems()
        del self.dir_list[:]
        del self.track_list[:]
        for item in os.listdir(self.path):
            if os.path.isdir(self.path + "/" + item): 
                self.dir_list.append(item)
            elif os.path.isfile(self.path + "/" +item) and self.get_codec(item) in [".wav", ".mp3"]:
                self.track_list.append(item)
        for item in self.dir_list:
            self.list_ctrl.InsertItem(self.index, "->" + item)
            self.index += 1
        
        for item in self.track_list:
            self.list_ctrl.InsertItem(self.index, item)
            self.index += 1
        if self.list_ctrl.GetItemCount() > 0:
            self.list_ctrl.Select(0)
        self.path_label.Clear()
        self.path_label.AppendText(self.path)

    def get_codec(self, path):
        if len(path) < 4:
            return
        return path[-4:]

    def on_key_load(self, channel):
        if self.list_ctrl.GetSelectedItemCount() != 1:
            pass
        elif self.list_ctrl.GetFirstSelected() < len(self.dir_list):
            self.path += "/" + self.list_ctrl.GetItemText(self.list_ctrl.GetFirstSelected())[2:]
            self.dir_lvl += 1
        elif self.list_ctrl.GetFirstSelected() < self.list_ctrl.GetItemCount():
            track_name = self.list_ctrl.GetItemText(self.list_ctrl.GetFirstSelected())
            if self.get_codec(self.path + "/" + track_name) == ".mp3" and not self.decode_is_running:
                self.new_track = [self.path_temp + "/" + track_name[:-3] + "wav", channel, self.get_codec(self.path + "/" + track_name)]
                self.decode_obj = self.player.decode_mp3(self.path + "/" + track_name, self.path_temp + "/" + track_name[:-3] + "wav")
                self.decode_is_running = True                
            elif self.get_codec(self.path + "/" + track_name) == ".wav":
                t = TrackLoader(self.player, self.path + "/" + track_name, channel)
                #self.player.load_track(self.path + "/" + track_name, channel)
                self.player.snd_view = True
        self.refresh_list_view()

    def on_key_left(self):
        if self.dir_lvl > 0:
            self.path = "/".join(self.path.split("/")[:-1])
            self.refresh_list_view()
            self.dir_lvl -= 1

    def on_key_pressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_NUMPAD0 or keycode == wx.WXK_RIGHT:
            self.on_key_load(0)
        elif keycode == wx.WXK_NUMPAD1:
            self.on_key_load(1)
        elif keycode == wx.WXK_LEFT:
            self.on_key_left()
        event.Skip()

class MyFrame(wx.Frame):
    def __init__(self, player):
        wx.Frame.__init__(self, None, style = wx.NO_BORDER | wx.CAPTION)
        self.box_sizer_v = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer_stat0 = wx.BoxSizer(wx.HORIZONTAL) 
        self.box_sizer_stat1 = wx.BoxSizer(wx.HORIZONTAL) 
        
        self.SetSizer(self.box_sizer_v)
        
        self.is_running = True
        self.new_input = ""
        self.cmd_state = ""
        self.cmd_chnl = ""
        self.player = player
        self.snd_view = [PyoGuiSndView(parent = self, size = (300, 50)), PyoGuiSndView(parent = self, size = (300, 50))]
        self.cmd = wx.TextCtrl(parent = self, style = wx.TE_PROCESS_ENTER)
        self.text = wx.TextCtrl(parent = self)
        self.timer = wx.Timer(self)
        self.pitch = [wx.TextCtrl(parent = self, value = "0.0%", style = wx.TE_READONLY), wx.TextCtrl(parent = self, value = "0.0%", style = wx.TE_READONLY)] 
        self.pos = [wx.TextCtrl(parent = self, value = "0:00/0:00", style = wx.TE_READONLY), wx.TextCtrl(parent = self, value = "0:00/0:00", style = wx.TE_READONLY)] 
    
        self.box_sizer_v.Add(self.cmd, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL)
        self.box_sizer_v.Add(self.text, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL)
        self.box_sizer_v.Add(self.box_sizer_stat0, 0, wx.ALL)
        self.box_sizer_v.Add(self.snd_view[0], 0, wx.ALL)
        self.box_sizer_v.Add(self.box_sizer_stat1, 0, wx.ALL)
        self.box_sizer_v.Add(self.snd_view[1], 0, wx.ALL)
        self.box_sizer_stat0.Add(self.pitch[0], wx.ALL)
        self.box_sizer_stat0.Add(self.pos[0], wx.ALL)
        self.box_sizer_stat1.Add(self.pitch[1], wx.ALL)
        self.box_sizer_stat1.Add(self.pos[1], wx.ALL)
        self.box_sizer_v.Fit(self)
        self.timer.Start(100)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.cmd.Bind(wx.EVT_TEXT_ENTER, self.new_cmd)

    def refresh_snd_view(self, channel):
        self.snd_view[channel].setTable(self.player.mono_table[channel])
        self.snd_view[channel].update()

    def new_cmd(self, event):
        self.new_input = self.cmd.GetLineText(0)
        if self.cmd_state == "":
            if self.new_input == "s0":
                self.player.start_stop(0)
                self.print_msg("", self.text)
            elif self.new_input == "s1":
                self.player.start_stop(1) 
                self.print_msg("", self.text)
            elif self.new_input == "pitch0":
                self.print_msg("pitch channel 0 between 0 and 1", self.text)
                self.cmd_state = "pitch"
                self.cmd_chnl = 0
            elif self.new_input == "pitch1":
                self.print_msg("pitch channel 1 between 0 and 1", self.text)
                self.cmd_state = "pitch"
                self.cmd_chnl = 1
            elif self.new_input == "pos0":
                self.print_msg("position channel 0 between 0 and 1", self.text)
                self.cmd_state = "pos"
                self.cmd_chnl = 0
            elif self.new_input == "pos1":
                self.print_msg("position channel 1 between 0 and 1", self.text)
                self.cmd_state = "pos"
                self.cmd_chnl = 1
            elif self.new_input == "jump0":
                self.print_msg("jump diff channel 0 between 0 and 1", self.text)
                self.cmd_state = "jump"
                self.cmd_chnl = 0
            elif self.new_input == "jump1":
                self.print_msg("jump diff channel 1 between 0 and 1", self.text)
                self.cmd_state = "jump"
                self.cmd_chnl = 1
            elif self.new_input == "low0":
                self.print_msg("low boost channel 0 between 0 and 1", self.text)
                self.cmd_state = "low"
                self.cmd_chnl = 0
            elif self.new_input == "low1":
                self.print_msg("low boost channel 1 between 0 and 1", self.text)
                self.cmd_state = "low"
                self.cmd_chnl = 1
            elif self.new_input == "mid0":
                self.print_msg("low boost channel 0 between 0 and 1", self.text)
                self.cmd_state = "mid"
                self.cmd_chnl = 0
            elif self.new_input == "mid1":
                self.print_msg("mid boost channel 1 between 0 and 1", self.text)
                self.cmd_state = "mid"
                self.cmd_chnl = 1
            elif self.new_input == "high0":
                self.print_msg("high boost channel 0 between 0 and 1", self.text)
                self.cmd_state = "high"
                self.cmd_chnl = 0
            elif self.new_input == "high1":
                self.print_msg("high boost channel 1 between 0 and 1", self.text)
                self.cmd_state = "high"
                self.cmd_chnl = 1
            else:
                self.cmd_state = ""
                self.print_msg("invalid input", self.text)
            self.cmd.Clear()
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
                self.print_msg("invalid input!!!!", self.text)
            self.cmd_state = ""
            self.print_msg("", self.text)
        
    def update(self, event):
        self.snd_view[0].setSelection(0, self.player.phasor[0].get())
        self.snd_view[1].setSelection(0, self.player.phasor[1].get())
        self.print_msg('{:+.1f}'.format((self.player.pitch[0] - 1) * 100) + "%", self.pitch[0])
        self.print_msg('{:+.1f}'.format((self.player.pitch[1] - 1) * 100) + "%", self.pitch[1])
        self.print_msg(self.sec_to_str(int(self.player.phasor[0].get() * self.player.table[0].getDur()), int(self.player.table[0].getDur())), self.pos[0])
        self.print_msg(self.sec_to_str(int(self.player.phasor[1].get() * self.player.table[1].getDur()), int(self.player.table[1].getDur())), self.pos[1])
        if self.player.refresh_snd[0]:
            self.refresh_snd_view(0)
            self.player.refresh_snd[0] = False
        
        if self.player.refresh_snd[1]:
            self.refresh_snd_view(1)
            self.player.refresh_snd[1] = False
    
    def print_msg(self, text, textctrl):
        textctrl.Clear()
        textctrl.AppendText(text)

    def sec_to_str(self, sec, dur):
        return str(int(sec/60)) + ":" + str(sec%60).zfill(2) + "/" + str(int(dur/60)) + ":" + str(dur%60).zfill(2)        

p = Player()
p.server.start()
app = wx.App()
frame = MyFrame(p).Show()
frame1 = BrowserFrame(p).Show()
app.MainLoop()
