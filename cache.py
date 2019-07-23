from lib import *
import config 
from pyo import *
import track_loading 
import concurrent.futures
import logging

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)

class Cache():
    def __init__(self) -> None:
        self.start = [0, 0]
        self.shared_table = [SharedTable(["/sharedl0", "/sharedr0"], True, int(config.chunk_size * config.cache_size * config.sample_rate)),
                        SharedTable(["/sharedl1", "/sharedr1"], True, int(config.chunk_size * config.cache_size * config.sample_rate))]
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
        self.is_loading = [False, False]
         
    def insert(self, path: str, channel: int, src_begin: int, size: int, back: bool = True, write_to_begin: bool = False) -> None: 
        # Error handling 
        if self.is_loading:
            logger.error("already loading")
            return
        if size > config.cache_size:
            logger.error("size greater than cache_size")
            return
        if write_to_begin and back:
            logger.error("invalid combination of bool parameters")
            return 

        # calculate position in cache where to start loading 
        dest_begin = 0
        if not write_to_begin:
            dest_begin = self.start[channel]
            self.start[channel] = dest_begin + size
            if not back:
                dest_begin = (self.start[channel] - size) % config.cache_size
                self.start[channel] = dest_begin

        # load either one continuous parts or two seperate parts into cache  
        if dest_begin + size > config.cache_size:
            future = self.executor.submit(track_loading.load, path, channel, src_begin, [config.cache_size - dest_begin, size - (config.cache_size - dest_begin)], [dest_begin, 0])
        else:
            future = self.executor.submit(track_loading.load, path, channel, src_begin, size, dest_begin)
    
        self.is_loading[channel] = True
        future.add_done_callback(self.done_loading)


    def done_loading(self, future) -> None:
        self.is_loading[future.result()] = False