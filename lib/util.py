import logging
import sys
from os import environ

LOG_LEVEL = environ.get("LOG_LEVEL", default="INFO")
LOG_PATH = environ.get("LOG_PATH", default="storage/logs/app.log")


def setup_logger():
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    for handler in [logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_PATH)]:
        handler.setFormatter(logFormatter)
        root_logger.addHandler(handler)
    logging.debug(f"LOG: {LOG_LEVEL}")


