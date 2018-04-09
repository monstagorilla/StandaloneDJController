from __future__ import division
from pyo import *
import sys
import os

def init():
    s = Server()
    s.setInOutDevice(7)
    s.boot()
    return s
   
s = init()
snd = SndTable('/home/monstagorilla/Documents/Coding/StandaloneDJController/test.wav')
p = Phasor(freq=snd.getRate()*1.1)
a = Pointer(table=snd, index = p, mul = 0.3)
n = Noise()
lowEq = EQ(input = a, boost = 1, freq = 125, q = 1, type = 1)
midEq = EQ(input = lowEq, boost = 1, freq = 1200, q = 0.5, type = 0) 
highEq = EQ(input = midEq, boost = 1, freq = 8000, q = 1, type =2).out()
lowEq.ctrl(title="low")
midEq.ctrl(title="mid")
highEq.ctrl(title="high")
#p.ctrl(title="pitch")
spec = Spectrum(highEq, size=1024)
s.gui(locals())

