# config/logger.py
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(to_file=False):
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)  # Set to INFO or WARNING for production

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create and add file handler if flag is set
    if to_file:
        fh = RotatingFileHandler('application.log', maxBytes=10485760, backupCount=5)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Add formatter to the handler
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)
