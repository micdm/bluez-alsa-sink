# -*- coding: utf8 -*-

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from dm_bas.logger import logger
from dm_bas.data import reader

A2DP_SINK_UUID = '0000110B-0000-1000-8000-00805F9B34FB'

SBC_CODEC = dbus.Byte(0x00)
SBC_CAPABILITIES = dbus.Array([dbus.Byte(0xff), dbus.Byte(0xff), dbus.Byte(2), dbus.Byte(64)])
SBC_CONFIGURATION = dbus.Array([dbus.Byte(0x21), dbus.Byte(0x15), dbus.Byte(2), dbus.Byte(32)])

class Endpoint(dbus.service.Object):
    
    DBUS_ADDRESS = '/dm_bas/endpoint'
    
    _instance = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            bus = _get_bus()
            cls._instance = Endpoint(bus, cls.DBUS_ADDRESS)
        return cls._instance
    
    @classmethod
    def get_file_descriptor(cls):
        endpoint = cls.get()
        logger.debug('acquiring endpoint transport')
        fd, _, _ = endpoint._transport.Acquire('r')
        return fd.take()
    
    @classmethod
    def release_file_descriptor(cls):
        endpoint = cls.get()
        logger.debug('releasing endpoint transport')
        endpoint._transport.Release('r')
    
    def __init__(self, *args, **kwargs):
        super(Endpoint, self).__init__(*args, **kwargs)
        self._transport = None

    @dbus.service.method('org.bluez.MediaEndpoint', in_signature='', out_signature='')
    def Release(self):
        logger.debug('releasing endpoint')
        self._transport = None

    @dbus.service.method('org.bluez.MediaEndpoint', in_signature='', out_signature='')
    def ClearConfiguration(self):
        logger.debug('clearing endpoint configuration')

    @dbus.service.method('org.bluez.MediaEndpoint', in_signature='oay', out_signature='')
    def SetConfiguration(self, transport_path, config):
        logger.debug('setting up endpoint configuration')
        bus = _get_bus()
        self._transport = dbus.Interface(bus.get_object('org.bluez', transport_path), 'org.bluez.MediaTransport')

    @dbus.service.method('org.bluez.MediaEndpoint', in_signature='ay', out_signature='ay')
    def SelectConfiguration(self, caps):
        logger.debug('selecting endpoint configuration')
        return SBC_CONFIGURATION

def _get_bus():
    return dbus.SystemBus()

def _get_default_adapter_path():
    bus = _get_bus()
    manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.bluez.Manager')
    return manager.DefaultAdapter()

def _get_default_adapter():
    bus = _get_bus()
    path = _get_default_adapter_path()
    return dbus.Interface(bus.get_object('org.bluez', path), 'org.bluez.Adapter')

def _get_media():
    bus = _get_bus()
    adapter_path = _get_default_adapter_path()
    return dbus.Interface(bus.get_object('org.bluez', adapter_path), 'org.bluez.Media')

def _register_endpoint():
    _ = Endpoint.get()
    properties = dbus.Dictionary({
        'UUID': A2DP_SINK_UUID,
        'Codec': SBC_CODEC,
        'Capabilities': SBC_CAPABILITIES
    })
    media = _get_media()
    media.RegisterEndpoint(Endpoint.DBUS_ADDRESS, properties)

def _get_device_path(device_id):
    adapter = _get_default_adapter()
    return adapter.FindDevice(device_id)

def _get_audio_source():
    bus = _get_bus()
    #TODO: найти подходящее устройство
    device_path = _get_device_path('38:E7:D8:3C:5A:0A')
    return dbus.Interface(bus.get_object('org.bluez', device_path), 'org.bluez.AudioSource')

class AudioSourceSubscriber(object):

    def __init__(self):
        self._state = None

    def on_property_changed(self, name, value):
        if name != 'State':
            logger.debug('unknown property "%s" changed on audio source', name)
            return
        logger.debug('audio source state changed to "%s"', value)
        if value in ('connected', 'disconnected'):
            if self._state == 'playing':
                Endpoint.release_file_descriptor()
                reader.set_file_descriptor(None)
        if value == 'playing':
            fd = Endpoint.get_file_descriptor()
            reader.set_file_descriptor(fd)
        self._state = value

def _subscribe_to_audio_source():
    audio_source = _get_audio_source()
    subscriber = AudioSourceSubscriber()
    audio_source.connect_to_signal('PropertyChanged', subscriber.on_property_changed)
    
def init():
    DBusGMainLoop(set_as_default=True)
    _register_endpoint()
    _subscribe_to_audio_source()
