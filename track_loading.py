from pyo import *
import time
import logging
import subprocess
import os
import numpy
import shutil
import ffmpeg
from scipy.io import wavfile

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


def load(path: str, channel: int):
    out, _ = (ffmpeg.input(path).output('pipe:', format='wav', ac=2, ar=44100).run(capture_stdout=True))
    raw_data = numpy.frombuffer(out, numpy.int16)
    norm_data = raw_data / raw_data.max(axis=0)
    if len(norm_data) % 2 == 0:
        norm_data = [(norm_data[::2]).tolist(), (norm_data[1::2]).tolist()]
    else:
        norm_data = [norm_data[:-1:2].tolist(), norm_data[1::2].tolist()]  # TODO different channel size

    table = NewTable(length=len(norm_data[0]) / 44100, init=norm_data, chnls=2)  # TODO use thread
    table.fadein(0.1)
    length = float(ffmpeg.probe(path)["format"]["duration"]) * 44100
    shared_table_c = SharedTable(["/sharedl{}".format(channel), "/sharedr{}".format(channel)], False, int(length))
    shared_table_c.copyData(table)
    return [path, channel]
