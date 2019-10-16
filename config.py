import logging

audio_device = 6
cache_size = 4  # cache size in chunks, has to be multiple of 2, at least 4
chunk_size = 11.88861678  # chunk size in seconds TODO: explain or calculate number
sample_rate = 44100  # sample rate in Hertz
# eq frequencies
frequency_low = 125
frequency_mid = 1200  # TODO good choice for frequencies?
frequency_high = 4000

system_partition_name = "sda"
logging_level = logging.DEBUG
release_mode = True