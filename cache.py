from lib import *
import config 
from pyo import *
import track_loading 
import concurrent.futures
import logging
import player

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)

class Cache:
    def __init__(self, player: player) -> None:
        self.start = [0, 0]
        self.shared_table = [SharedTable(["/sharedl0", "/sharedr0"], True, int(config.chunk_size * config.cache_size * config.sample_rate)),
                        SharedTable(["/sharedl1", "/sharedr1"], True, int(config.chunk_size * config.cache_size * config.sample_rate))]
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
        self.is_loading = [False, False]
        self.player = player        
         
    def insert(self, path: str, channel: int, src_begin: int, size: int, back: bool = True, is_new_track: bool = False) -> None: # write_to_begin: if cache should be filled from the begin
                                                                                                                                   # back: if cache should be inserted after starting point 
        # Error handling 
        if self.is_loading:
            logger.error("already loading")
            return
        if size > config.cache_size:
            logger.error("size greater than cache_size")
            return
        #?????
        if is_new_track and not back: # it makes no sense to write explicite a new new track backwards from the beginning
            logger.error("invalid combination of bool parameters")
            return 

        # calculate position in cache where to start loading 
        dest_begin = 0
        if not is_new_track: # if to write from actual starting point
            dest_begin = self.start[channel]
            self.start[channel] = dest_begin + size
            if not back:
                dest_begin = (self.start[channel] - size) % config.cache_size
                self.start[channel] = dest_begin

        # load either one continuous parts or two seperate parts into cache  
        if dest_begin + size > config.cache_size:
            future = self.executor.submit(track_loading.load, path, channel, src_begin, [config.cache_size - dest_begin, size - (config.cache_size - dest_begin)], [dest_begin, 0], back)
        else:
            future = self.executor.submit(track_loading.load, path, channel, src_begin, size, dest_begin, back)
    
        self.is_loading[channel] = True
        if is_new_track:
            future.add_done_callback(self.player.done_new_track)
        else:    
            future.add_done_callback(self.player.done_loading)