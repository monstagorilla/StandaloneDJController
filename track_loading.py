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

def load(path: str, channel: int, start: int, stop: int, tx_wav_data: Connection):
    # call rust function for controlled memory management and enhanced speed
    # audio samples are always in memory once

    # calculate start, stop time 
    start_f = start * 11.88861678
    stop_f = stop * 11.88861678
    result_data = rustlib.load_track(path, str(start), str(stop), channel)
    table = DataTable(size=len(result_data[0]), init=result_data, chnls=2)
    table.fadein(0.1)  # prevent noise at beginning
                       # TODO: find reason for noise, maybe metadata interpreted as audio samples
    
    # calculate length using metadata from ffmpeg probe
    try:
        length = float(ffmpeg.probe(path)["format"]["duration"]) * 44100
    except Exception as e:
        logger.error(e)
        return
    
    # use shared table object for accesing from different processes because pyo table objects are not pickable  
    shared_table_c = SharedTable(["/sharedl{}".format(channel), "/sharedr{}".format(channel)], False, int(length))
    shared_table_c.copyData(table)
    return [path, channel]
