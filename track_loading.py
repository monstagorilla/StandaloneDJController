from pyo import *
import time
import logging
import subprocess
import os
import numpy
import shutil
from scipy.io import wavfile

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)


def decoding_mp3(path: str, path_temp: str) -> str:
    name = "/".join(path.split("/")[-1:])

    # init temp dir
    if os.path.isdir(path_temp):
        clear_temp_dir(path_temp)
    else:
        os.mkdir(path_temp)

    decode_obj = subprocess.Popen(["ffmpeg", "-i", path, path_temp + "/" + name[:-3] + "wav"])
    count = 0
    while decode_obj.poll() is None:
        time.sleep(0.1)
        if count > 1000:
            logger.error("timeout")
            return ""
        count += 1
    return path_temp + "/" + name[:-3] + "wav"


def load(path: str, channel: int):
    if len(path) < 3:
        logger.error("path too short")
        return None
    codec = path[-3:]

    if codec == "mp3":
        path_temp = os.path.expanduser("~/standalone_dj_controller_temp")
        path_new = decoding_mp3(path, path_temp)
        if path_new != "":
            # TODO dont use sample rate?
            raw_data = wavfile.read(path_new)[1]
            norm_data = []
            max_value = numpy.max(raw_data, axis=0)
            for x in raw_data:
                norm_data.append(x / max_value)

            #table = SndTable(path=path_new)
            clear_temp_dir(path_temp)
            return [numpy.asarray(norm_data), path, channel]  # TODO better error handling
    elif codec == "wav":
        #return [SndTable(path=path), path, channel]
        raw_data = wavfile.read(path)[1]
        norm_data = []
        max_value = numpy.max(raw_data, axis=0)
        #max_value = raw_data.max
        for x in raw_data:
            norm_data.append(x/max_value)
        return [numpy.asarray(norm_data), path, channel]  # TODO better error handling


def get_list_from_wav(path: str):
    return

def clear_temp_dir(path_temp: str) -> None:
    for the_file in os.listdir(path_temp):
        file_path = os.path.join(path_temp, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(e)
