# CLEAN

from pyo import *
import logging
import numpy
import ffmpeg
from multiprocessing.connection import Connection
import gc
import rustlib
# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)

def load(path: str, channel: int, tx_wav_data: Connection):
    #process = (ffmpeg.input(path).output('pipe:', format='wav', ac=2, ar=44100).run_async(pipe_stdout=True, pipe_stderr=True))
    #out, _ = process.communicate()
    #if not out:
    #    logger.error("loading failed")
    #    return
    #
    #raw_data = numpy.ndarray(buffer=out, shape=(int(len(out)/4), 2), dtype=numpy.int16)
    #try:
    #    data = [raw_data[:, 0] / raw_data[:, 0].max(axis=0), raw_data[:, 0] / raw_data[:, 0].max(axis=0)]
    #except Exception as e:
    #    logger.error(e)
    #    return
    #process.kill()
    #del raw_data
    #del out
    #gc.collect()
    #result_data = [data[0].tolist()]
    #del data[0]
    #gc.collect()
    #result_data.append(data[0].tolist())
    #del data[0]
    #del data
    #gc.collect()
    result_data = rustlib.load_track(path, channel)
    #print(type(result_data[0]))
    #print(max(result_data))
    ##result_data[1].append(0.0)
    
    #print(result_data[0][10000])
    table = DataTable(size=len(result_data[0]), init=result_data, chnls=2)
    table.fadein(0.1)  # prevent noise at beginning TODO: find reason for noise
    #table.normalize()

    #print(max(table.getTable()))

    #for i in range(400000, 400300):
    #    print(type(table.getTable()[i]))
    
    #tx_wav_data.send((result_data, channel))
    try:
        length = float(ffmpeg.probe(path)["format"]["duration"]) * 44100
    except Exception as e:
        logger.error(e)
        return
    shared_table_c = SharedTable(["/sharedl{}".format(channel), "/sharedr{}".format(channel)], False, int(length))
    shared_table_c.copyData(table)
    # del table
    # gc.collect()
    return [path, channel]
