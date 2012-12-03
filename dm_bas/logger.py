# -*- coding: utf8 -*-

import logging

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def set_logger_verbose():
    logger.setLevel(logging.DEBUG)
    logger.debug('logger is now verbose')
