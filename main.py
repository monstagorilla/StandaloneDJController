#!/usr/bin/env python3

from gui import GUIApp
from kivy.core.window import Window
import config
import sys
import logging

# Logging
logger = logging.getLogger(__name__)  # TODO redundant code in logger setup(every module)
logger.setLevel(config.logging_level)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
stream_handler.setFormatter(formatter)

if __name__ == '__main__':
    app = GUIApp()
    # Window.fullscreen = True
    # Window.size = [600, 300]

    try:
        app.run()
    except Exception as e:
        logger.error(e)
        if config.release_mode:
            pass
