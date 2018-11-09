#!/usr/bin/env python3
from gui import GUIApp


# possible issues: simultanious track loading, audio artefects when switching window (jack problem???),
# audio artefacts when loading?
# TODO: error handling, pretty gui, filter/effects

# class BrowserFrame(wx.Frame):
#     def __init__(self, player):
#         wx.Frame.__init__(self, None,  style = wx.NO_BORDER | wx.CAPTION)
#
#         self.path = ""
#         self.path_root = ""
#         self.path_temp = os.path.expanduser("~/temp_standalone_dj_controller")
#
#         self.player = player
#         self.usb = USB_Manager()
#         self.decoder = Decoder(self.path_temp, player, self.clear_temp_dir)
#
#         #init temp dir
#         if os.path.isdir(self.path_temp):
#             self.clear_temp_dir()
#         else:
#             os.mkdir(self.path_temp)
#
#         self.timer = wx.Timer(self)
#         self.timer.Start(100)
#         self.timer1 = wx.Timer(self)
#         self.timer1.Start(100)
#         self.timer2 = wx.Timer(self)
#         self.timer2.Start(100)  #possible longer intervals
#         self.Bind(wx.EVT_TIMER, self.decoder.update_decoder, self.timer)
#         self.Bind(wx.EVT_TIMER, self.usb.update_state, self.timer1)
#         self.Bind(wx.EVT_TIMER, self.update_mountpoint, self.timer2)
#
#         self.dir_list = []
#         self.track_list = []
#         self.index = 0
#         self.dir_lvl = 0
#
#         self.box_sizer_v = wx.BoxSizer(wx.VERTICAL)
#         self.SetSizer(self.box_sizer_v)
#
#         self.list_ctrl = wx.ListCtrl(parent = self, size = (400, 300), style = wx.LC_REPORT | wx.LC_SINGLE_SEL)
#         self.list_ctrl.InsertColumn(0, "Title", width = 200)
#         self.path_label = wx.TextCtrl(parent = self, size = (400, -1), style = wx.TE_READONLY, value = self.path)
#         self.refresh_list_view()
#
#         self.box_sizer_v.Add(self.path_label, 0, wx.ALL)
#         self.box_sizer_v.Add(self.list_ctrl, 0, wx.ALL)
#         self.box_sizer_v.Fit(self)
#
#         self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_pressed)
#         self.list_ctrl.SetFocus()
#
#
#
#
#
#
#
#     def on_key_load(self, channel):
#         if self.list_ctrl.GetSelectedItemCount() != 1:
#             pass
#         elif self.list_ctrl.GetFirstSelected() < len(self.dir_list):
#             self.path += "/" + self.list_ctrl.GetItemText(self.list_ctrl.GetFirstSelected())[2:]
#             self.dir_lvl += 1
#         elif self.list_ctrl.GetFirstSelected() < self.list_ctrl.GetItemCount():
#             track_name = self.list_ctrl.GetItemText(self.list_ctrl.GetFirstSelected())
#             print(track_name)
#             if self.get_codec(self.path + "/" + track_name) == ".mp3" and not self.decoder.decode_is_running:
#                 new_track = [self.path + "/" + track_name, channel, self.get_codec(self.path + "/" + track_name)]
#                 self.decoder.load_mp3(track_name, new_track)
#                 print("new track: " + str(new_track))
#             elif self.get_codec(self.path + "/" + track_name) == ".wav":
#                 t = TrackLoader(self.player, self.path + "/" + track_name, channel, self.clear_temp_dir)
#                 self.player.snd_view = True
#         self.refresh_list_view()
#
#     def on_key_left(self):
#         if self.dir_lvl > 0:
#             self.path = "/".join(self.path.split("/")[:-1])
#             self.refresh_list_view()
#             self.dir_lvl -= 1
#
#     def on_key_pressed(self, event):
#         if not self.usb.device_connected:
#             return
#         keycode = event.GetKeyCode()
#         if keycode == wx.WXK_NUMPAD0:
#             self.on_key_load(0)
#         elif keycode == wx.WXK_NUMPAD1:
#             self.on_key_load(1)
#         elif keycode == wx.WXK_LEFT:
#             self.on_key_left()
#         event.Skip()
#
#
# class MyFrame(wx.Frame):
#     def __init__(self, player):
#         wx.Frame.__init__(self, None, style = wx.NO_BORDER | wx.CAPTION)
#         self.box_sizer_v = wx.BoxSizer(wx.VERTICAL)
#         self.box_sizer_stat0 = wx.BoxSizer(wx.HORIZONTAL)
#         self.box_sizer_stat1 = wx.BoxSizer(wx.HORIZONTAL)
#
#         self.SetSizer(self.box_sizer_v)
#
#         self.is_running = True
#         self.new_input = ""
#         self.cmd_state = ""
#         self.cmd_chnl = ""
#         self.player = player
#         self.snd_view = [PyoGuiSndView(parent = self, size = (300, 50)), PyoGuiSndView(parent = self, size = (300, 50))]
#         self.cmd = wx.TextCtrl(parent = self, style = wx.TE_PROCESS_ENTER)
#         self.text = wx.TextCtrl(parent = self)
#         self.timer = wx.Timer(self)
#         self.pitch = [wx.TextCtrl(parent = self, value = "0.0%", style = wx.TE_READONLY), wx.TextCtrl(parent = self, value = "0.0%", style = wx.TE_READONLY)]
#         self.pos = [wx.TextCtrl(parent = self, value = "0:00/0:00", style = wx.TE_READONLY), wx.TextCtrl(parent = self, value = "0:00/0:00", style = wx.TE_READONLY)]
#         self.title = [wx.TextCtrl(parent = self, value = "", style = wx.TE_READONLY), wx.TextCtrl(parent = self, value = "", style = wx.TE_READONLY)]
#         self.box_sizer_v.Add(self.cmd, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL)
#         self.box_sizer_v.Add(self.text, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL)
#         self.box_sizer_v.Add(self.box_sizer_stat0, 0, wx.ALL)
#         self.box_sizer_v.Add(self.snd_view[0], 0, wx.ALL)
#         self.box_sizer_v.Add(self.box_sizer_stat1, 0, wx.ALL)
#         self.box_sizer_v.Add(self.snd_view[1], 0, wx.ALL)
#         self.box_sizer_stat0.Add(self.pitch[0], wx.ALL)
#         self.box_sizer_stat0.Add(self.pos[0], wx.ALL)
#         self.box_sizer_stat0.Add(self.title[0], wx.ALL)
#         self.box_sizer_stat1.Add(self.pitch[1], wx.ALL)
#         self.box_sizer_stat1.Add(self.pos[1], wx.ALL)
#         self.box_sizer_stat1.Add(self.title[1], wx.ALL)
#         self.box_sizer_v.Fit(self)
#         self.timer.Start(100)
#         self.Bind(wx.EVT_TIMER, self.update, self.timer)
#         self.cmd.Bind(wx.EVT_TEXT_ENTER, self.new_cmd)
#
#     def refresh_snd_view(self, channel):
#         self.snd_view[channel].setTable(self.player.mono_table[channel])
#         self.snd_view[channel].update()
#
#
#     @staticmethod
#     def sec_to_str(self, sec, dur):
#         return str(int(sec/60)) + ":" + str(sec%60).zfill(2) + "/" + str(int(dur/60)) + ":" + str(dur%60).zfill(2)


if __name__ == '__main__':
    app = GUIApp()
    #Window.fullscreen = True
    #Window.size = [600, 300]
    app.run()






# if __name__ == "__main__":
#     p = Player()
#     p.server.start()
#     app = wx.App()
#     frame = MyFrame(p).Show()
#     frame1 = BrowserFrame(p).Show()
#     app.MainLoop()




                    #     if self.cmd_state == "":
                    #         if self.new_input == "s0":
                    #             self.player.start_stop(0)
                    #             self.print_msg("", self.text)
                    #         elif self.new_input == "s1":
                    #             self.player.start_stop(1)
                    #             self.print_msg("", self.text)
                    #         elif self.new_input == "pitch0":
                    #             self.print_msg("pitch channel 0 between 0 and 1", self.text)
                    #             self.cmd_state = "pitch"
                    #             self.cmd_chnl = 0
                    #         elif self.new_input == "pitch1":
                    #             self.print_msg("pitch channel 1 between 0 and 1", self.text)


                    # def new_cmd(self, event):
                    #     self.new_input = self.cmd.GetLineText(0)
                    #             self.cmd_state = "pitch"
                    #             self.cmd_chnl = 1
                    #         elif self.new_input == "pos0":
                    #             self.print_msg("position channel 0 between 0 and 1", self.text)
                    #             self.cmd_state = "pos"
                    #             self.cmd_chnl = 0
                    #         elif self.new_input == "pos1":
                    #             self.print_msg("position channel 1 between 0 and 1", self.text)
                    #             self.cmd_state = "pos"
                    #             self.cmd_chnl = 1
                    #         elif self.new_input == "jump0":
                    #             self.print_msg("jump diff channel 0 between 0 and 1", self.text)
                    #             self.cmd_state = "jump"
                    #             self.cmd_chnl = 0
                    #         elif self.new_input == "jump1":
                    #             self.print_msg("jump diff channel 1 between 0 and 1", self.text)
                    #             self.cmd_state = "jump"
                    #             self.cmd_chnl = 1
                    #         elif self.new_input == "low0":
                    #             self.print_msg("low boost channel 0 between 0 and 1", self.text)
                    #             self.cmd_state = "low"
                    #             self.cmd_chnl = 0
                    #         elif self.new_input == "low1":
                    #             self.print_msg("low boost channel 1 between 0 and 1", self.text)
                    #             self.cmd_state = "low"
                    #             self.cmd_chnl = 1
                    #         elif self.new_input == "mid0":
                    #             self.print_msg("low boost channel 0 between 0 and 1", self.text)
                    #             self.cmd_state = "mid"
                    #             self.cmd_chnl = 0
                    #         elif self.new_input == "mid1":
                    #             self.print_msg("mid boost channel 1 between 0 and 1", self.text)
                    #             self.cmd_state = "mid"
                    #             self.cmd_chnl = 1
                    #         elif self.new_input == "high0":
                    #             self.print_msg("high boost channel 0 between 0 and 1", self.text)
                    #             self.cmd_state = "high"
                    #             self.cmd_chnl = 0
                    #         elif self.new_input == "high1":
                    #             self.print_msg("high boost channel 1 between 0 and 1", self.text)
                    #             self.cmd_state = "high"
                    #             self.cmd_chnl = 1
                    #         else:
                    #             self.cmd_state = ""
                    #             self.print_msg("invalid input", self.text)
                    #         self.cmd.Clear()
                    #     else:
                    #         try:
                    #             if self.cmd_state == "pitch":
                    #                 self.player.set_pitch(float(self.new_input), self.cmd_chnl)
                    #             elif self.cmd_state == "pos":
                    #                 self.player.set_position(float(self.new_input), self.cmd_chnl)
                    #             elif self.cmd_state == "jump":
                    #                 self.player.jump_position(float(self.new_input), self.cmd_chnl)
                    #                 self.player.set_eq(self.player.midEq[self.cmd_chnl], float(self.new_input))
                    #             elif self.cmd_state == "high":
                    #                 self.player.set_eq(self.player.highEq[self.cmd_chnl], float(self.new_input))
                    #             elif self.cmd_state == "quit":
                    #                 print("quit")
                    #         except:
                    #             self.print_msg("invalid input!!!!", self.text)
                    #         self.cmd_state = ""
                    #         self.print_msg("", self.text)

                    # def update(self, event):
                    #     self.snd_view[0].setSelection(0, self.player.phasor[0].get())
                    #     self.snd_view[1].setSelection(0, self.player.phasor[1].get())
                    #     self.print_msg('{:+.1f}'.format((self.player.pitch[0] - 1) * 100) + "%", self.pitch[0])
                    #     self.print_msg('{:+.1f}'.format((self.player.pitch[1] - 1) * 100) + "%", self.pitch[1])
                    #     self.print_msg(self.sec_to_str(int(self.player.phasor[0].get() * self.player.table[0].getDur()), int(self.player.table[0].getDur())), self.pos[0])
                    #     self.print_msg(self.sec_to_str(int(self.player.phasor[1].get() * self.player.table[1].getDur()), int(self.player.table[1].getDur())), self.pos[1])
                    #     self.print_msg(self.player.title[0], self.title[0])
                    #     self.print_msg(self.player.title[1], self.title[1])
                    #     if self.player.refresh_snd[0]:
                    #         self.refresh_snd_view(0)
                    #         self.player.refresh_snd[0] = False
                    #
                    #     if self.player.refresh_snd[1]:
                    #         self.refresh_snd_view(1)
                    #         self.player.refresh_snd[1] = False

                    # def print_msg(self, text, textctrl):
                    #     textctrl.Clear()
                    #     textctrl.AppendText(text)