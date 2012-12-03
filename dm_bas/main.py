# -*- coding: utf8 -*-

import gobject

from dm_bas.dbus_stuff import init as init_dbus
from dm_bas.logger import logger, set_logger_verbose
from dm_bas.data import init as init_data_handling

def _start_loop():
    loop = gobject.MainLoop()
    try:
        logger.debug('starting main loop')
        loop.run()
    except KeyboardInterrupt:
        logger.debug('exiting')
        loop.quit()
        
def init():
    set_logger_verbose()
    init_data_handling()
    init_dbus()
    _start_loop()
