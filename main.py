from pyo import *
s = Server()
s.setInOutDevice(7)
s.boot()
path1 = "/home/monstagorilla/Documents/Coding/StandaloneDJController/test.wav"
path2 = "/home/monstagorilla/Documents/Coding/StandaloneDJController/test2.wav"
t = SndTable(path1)
freq = t.getRate()
osc = Osc(table = t, freq = freq, mul = 0.4).out()
s.gui(locals())
