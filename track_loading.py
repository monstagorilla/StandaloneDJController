from pyo import SharedTable, DataTable
import logging
import numpy
import ffmpeg
import multiprocessing
import gc
import rustlib
import math
from lib import chunks_to_time, time_to_chunks
import config
import sys


# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter) 

#class Track_Loader(multiprocessing.Process):     
    #def __init__(self, channel: int) -> None:#
    #    super(Track_Loader, self).__init__()
    #    self.channel = channel

# call rust function for controlled memory management and enhanced speed
# audio samples are always in memory once
# calculate different fractures

def load(path: str, channel: int, src_begin: int, size: list, dest_begin: list, back: bool) -> [int, int]:
    if len(size) != len(dest_begin):
        logger.error("different list sizes")

    total_size = 0
    for x in size: 
        total_size += x

    # TODO extend multi list result to rust function
    result_data = rustlib.load_track(path, str(chunks_to_time(src_begin)), str(chunks_to_time(src_begin + total_size)))
    #table.fadein(0.1)  # prevent noise at beginning # TODO: find reason for noise, maybe metadata interpreted as audio samples

    # use shared table object for accesing from different processes because pyo table objects are not pickable  
    shared_table_c = SharedTable(name=["/sharedl{}".format(channel), "/sharedr{}".format(channel)], create=False, size=chunks_to_time(total_size) * config.sample_rate)   

    for i in range(0, len(dest_begin)): 
        table = DataTable(size=chunks_to_time(size[i]) * config.sample_rate, 
                        init=[result_data[0][chunks_to_time(dest_begin[i]) * config.sample_rate: chunks_to_time(dest_begin[i] + size[i]) * config.sample_rate],
                            result_data[1][chunks_to_time(dest_begin[i]) * config.sample_rate: chunks_to_time(dest_begin[i] + size[i]) * config.sample_rate]], 
                        chnls=2)
    
        shared_table_c.copyData(table=table, 
                                destpos = chunks_to_time(dest_begin[i]) * config.sample_rate)
    if back:
        return [channel, total_size]
    else:
        return [channel, -total_size]

def load_new(path: str, channel: int, src_begin: int, size: list, dest_begin: list, back: bool) -> [int, int, str]:
    result = load(path, channel, src_begin, size, dest_begin, back)
    result.append(path)
    return result