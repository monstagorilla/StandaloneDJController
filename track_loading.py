# CLEAN

from pyo import *
import logging
import numpy
import ffmpeg
from multiprocessing.connection import Connection

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


def load(path: str, channel: int, tx_wav_data: Connection):
    out, _ = (ffmpeg.input(path).output('pipe:', format='wav', ac=2, ar=44100).run(capture_stdout=True))
    if not out:
        logger.error("loading failed")
        return
    raw_data = numpy.frombuffer(out, numpy.int16)
    try:
        norm_data = raw_data / raw_data.max(axis=0)
    except Exception as e:
        logger.error(e)
        return
    if len(norm_data) % 2 == 0:
        norm_data = [norm_data[::2], norm_data[1::2]]
    else:
        norm_data = [norm_data[:-1:2], norm_data[1::2]]
    tx_wav_data.send(((norm_data[0] + norm_data[1]) / 2, channel))

    table = DataTable(size=len(norm_data[0]), init=[norm_data[0].tolist(), norm_data[1].tolist()], chnls=2)
    table.fadein(0.1)
    try:
        length = float(ffmpeg.probe(path)["format"]["duration"]) * 44100
    except Exception as e:
        logger.error(e)
        return
    shared_table_c = SharedTable(["/sharedl{}".format(channel), "/sharedr{}".format(channel)], False, int(length))
    shared_table_c.copyData(table)
    return [path, channel]
