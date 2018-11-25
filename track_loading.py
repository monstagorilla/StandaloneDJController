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


def load_track(path: str, channel: int, visual_width: int):
    out, _ = (ffmpeg.input(path).output('pipe:', format='wav', ac=2, ar=44100).run(capture_stdout=True))
    raw_data = numpy.frombuffer(out, numpy.int16)
    norm_data = raw_data / raw_data.max(axis=0)
    if len(norm_data) % 2 == 0:
        result_data = [(norm_data[::2]).tolist(), (norm_data[1::2]).tolist()]
    else:
        result_data = [norm_data[:-1:2].tolist(), norm_data[1::2].tolist()]  # TODO different channel size

    if visual_width > 0:
        chunk_size = int(len(result_data[0]) / visual_width)
    else:
        logger.warning("width = 0 -> cannot divide")
        return
    mean_data = []
    for x in range(0, int(visual_width)):
        try:
            mean_data.append(numpy.mean(result_data[0][x * chunk_size: (x + 3) * chunk_size]))
        except Exception as e:
            logger.warning(e)

    return [result_data, path, channel, mean_data]
