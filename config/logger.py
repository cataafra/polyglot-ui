# config/logger.py
import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)  # Set to INFO or WARNING for production

    # Create file handler which logs even debug messages
    fh = RotatingFileHandler('application.log', maxBytes=10485760, backupCount=5)
    fh.setLevel(logging.DEBUG)  # Adjust as necessary for file handler

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # Adjust as necessary for console output

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
