# CHECKED
from lib import *
import config 
from pyo import *
import track_loading 
import concurrent.futures
import logging
from player import Player

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(config.logging_level)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)

# ring buffer implementation
# insert chunks at the start or end of the actual buffer start
# call track_loading for reading samples from disk


class Cache:
    def __init__(self, player: Player) -> None:
        self.start = [0, 0]
        logger.debug("size shared table init: " + str(int(config.chunk_size * config.cache_size * config.sample_rate)))
        self.shared_table = [SharedTable(["/sharedl0", "/sharedr0"], True,
                                         int(config.chunk_size * config.cache_size * config.sample_rate)),
                             SharedTable(["/sharedl1", "/sharedr1"], True,
                                         int(config.chunk_size * config.cache_size * config.sample_rate))]
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
        self.is_loading = [False, False]
        self.player = player

    # write_to_begin: if cache should be filled from the begin
    # back: if cache should be inserted after starting point
    def insert(self, path: str, channel: int, src_begin: int, size: int, back: bool = True,
               is_new_track: bool = False) -> None:
        # Error handling
        if self.is_loading[channel]:  # TODO: stop loading if new track
            logger.debug("already loading")
            return
        assert not size > config.cache_size
        if is_new_track:
            assert back  # it makes no sense to write explicit a new new track backwards from the beginning

        # calculate position in cache where to start loading
        dest_begin = 0
        if not is_new_track:  # if to write from actual starting point
            if back:
                dest_begin = self.start[channel]
                self.start[channel] = dest_begin + size
            else:
                dest_begin = (self.start[channel] - size) % config.cache_size
                self.start[channel] = dest_begin

        # load either one continuous parts or two separate parts into cache
        try:
            if dest_begin + size < config.cache_size:
                if is_new_track:
                    future = self.executor.submit(track_loading.load_new, path, channel, src_begin, [size],
                                                  [dest_begin], back)
                else:
                    future = self.executor.submit(track_loading.load, path, channel, src_begin, [size], [dest_begin],
                                                  back)
            else:
                future = self.executor.submit(track_loading.load, path, channel, src_begin,
                                              [config.cache_size - dest_begin, size - (config.cache_size - dest_begin)],
                                              [dest_begin, 0], back)
        except Exception as e:
            logger.error(e)
            return
        self.is_loading[channel] = True

        if is_new_track:
            future.add_done_callback(self.player.done_new_track)
        else:
            future.add_done_callback(self.player.done_cache_update)
