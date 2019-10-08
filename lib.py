from math import ceil, copysign, floor
import config
import ffmpeg
import logging
import sys

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(config.logging_level)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


# Conversions between chunks and seconds
# CHECKED
def chunks_to_time(chunks: int) -> float:
    assert(chunks is not None)

    return chunks * config.chunk_size


# CHECKED
def time_to_chunks(time: float) -> int:
    assert(time is not None)

    return int(copysign(floor(abs(time) / config.chunk_size), time))


def get_dur(path: str) -> float:
    assert(path is not "" and path is not None)

    try:
        length = float(ffmpeg.probe(path)["format"]["duration"]) * config.sample_rate  # TODO: store info once
    except Exception as e:
        logger.error(e)
        return 0.0
    return length


# Functions for string representation in GUI

def pitch_to_str(pitch: float) -> str:
    assert(pitch is not None)

    return "{0}{1:.1f}%".format(("+" if pitch >= 1 else ""), (pitch - 1) * 100)


def pos_to_str(sec: float, dur: float) -> str:
    assert(sec is not None)
    assert(dur is not None)    
    
    return "{}:{}/{}:{}".format(str(int(sec / 60)), str(int(sec) % 60).zfill(2), str(int(dur / 60)), 
                                str(int(dur) % 60).zfill(2))
