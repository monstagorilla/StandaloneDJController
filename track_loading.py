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
logger.setLevel(config.logging_level)
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
    assert(path is not None)
    assert (channel is not None)
    assert (src_begin is not None)
    assert (size is not None)
    assert (dest_begin is not None)
    assert (back is not None)

    #size not 0?????

    if len(size) != len(dest_begin):
        logger.error("different list sizes")

    total_size = 0
    for x in size: 
        total_size += x

    # TODO extend multi list result to rust function
    result_data = rustlib.load_track(path, str(chunks_to_time(src_begin)), str(chunks_to_time(src_begin + total_size)))

    # use shared table object for accesing from different processes because pyo table objects are not pickable
    shared_table_c = SharedTable(name=["/sharedl{}".format(channel), "/sharedr{}".format(channel)], create=False, size=int(chunks_to_time(total_size) * config.sample_rate))

    for i in range(0, len(dest_begin)):
        table = DataTable(size=int(size[i] * config.sample_rate * config.chunk_size),
                          init=[result_data[0][int(chunks_to_time(int(dest_begin[i])) * config.sample_rate): int(chunks_to_time(int(dest_begin[i]) + int(size[i])) * config.sample_rate)],
                                result_data[1][int(chunks_to_time(int(dest_begin[i])) * config.sample_rate): int(chunks_to_time(int(dest_begin[i]) + int(size[i])) * config.sample_rate)]],
                      chnls=2)


        print("reached here")
        #table.fadein(0.5)  # prevent noise at beginning # TODO: find reason for noise, maybe metadata interpreted as audio samples
        shared_table_c.copyData(table=table,
                                destpos=int(chunks_to_time(int(dest_begin[i])) * config.sample_rate))
    if back:
        return [channel, total_size]
    else:
        return [channel, -total_size]


def load_new(path: str, channel: int, src_begin: int, size: list, dest_begin: list, back: bool) -> [int, int, str]:
    result = load(path, channel, int(src_begin), size, dest_begin, back)
    result.append(path)
    print("LISTE result")
    print(result)
    return result
