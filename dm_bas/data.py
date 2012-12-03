# -*- coding: utf8 -*-

import os

import alsaaudio
import gobject

from dm_bas.logger import logger
import dm_bas.pysbc as pysbc

class SbcToPcmDecoder(object):
    
    PACKET_LENGTH = 119
    
    def __init__(self):
        logger.debug('initializing pysbc')
        pysbc.init()
        
    def __del__(self):
        logger.debug('deinitializing pysbc')
        #TODO: деинициализировать иначе
        pysbc.deinit()

    def decode(self, data):
        chunks = []
        while data:
            decoded = pysbc.decode(data[:self.PACKET_LENGTH])
            chunks.append(decoded)
            data = data[self.PACKET_LENGTH:]
        return ''.join(chunks)
decoder = SbcToPcmDecoder()

class PcmPlayer(object):

    # Размер семпла * количество каналов * магическое 10:
    CHUNK_SIZE = 16 * 2 * 10

    def __init__(self):
        self._pcm = self._get_pcm()
        
    def _get_pcm(self):
        pcm = alsaaudio.PCM()
        pcm.setchannels(2)
        pcm.setrate(44100)
        pcm.setformat(alsaaudio.PCM_FORMAT_S16_BE)
        return pcm
    
    def play(self, data):
        while data:
            self._pcm.write(data[:self.CHUNK_SIZE])
            data = data[self.CHUNK_SIZE:]
player = PcmPlayer()

class DataReader(object):
    
    FRAME_MARKER = chr(0x9C)
    HEADER_SIZE = 13

    def __init__(self):
        self._fd = None

    def set_file_descriptor(self, fd):
        self._fd = fd
        
    def read(self):
        if not self._fd:
            return None
        try:
            data = os.read(self._fd, 4096)
            position = self.HEADER_SIZE
            if data[position] != self.FRAME_MARKER:
                logger.debug('marker not found')
                return None
            return data[position:]
        except OSError:
            return None
reader = DataReader()

def _on_tick():
    data = reader.read()
    if data is None:
        return True
    decoded = decoder.decode(data)
    player.play(decoded)
    return True

def init():
    gobject.timeout_add(1, _on_tick)
