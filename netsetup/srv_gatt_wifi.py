#!/usr/bin/env python
#
# Copyright (c) 2019, CESAR. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import logging
import dbus
import struct
from dbus.service import method as dbus_method

from ble_util.gatt_service import Service
from ble_util.characteristic import Characteristic
from ble_util.errors import InvalidValueLengthException


def convert_array_to_str(array):
    return ''.join(chr(i) for i in array)


class WifiService(Service):
    UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900e40"

    def __monitor_characteristic_changed(self, index, on_changed):
        return self.bus.add_signal_receiver(
                path=self.characteristics[index].get_path(),
                dbus_interface=dbus.PROPERTIES_IFACE,
                handler_function=on_changed,
                signal_name='PropertiesChanged')

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.UUID, True)
        self.add_characteristic(SSIDCharacteristic(bus, 0, self))

        self.ssid_signal = self.__monitor_characteristic_changed(
            0, self.__on_ssid_changed)

    def __on_ssid_changed(self, interface, changed, invalidated):
        self.ssid = changed['Value']
        logging.info('SSID changed to %s' % convert_array_to_str(self.ssid))


class SSIDCharacteristic(Characteristic):
    SSID_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d41"

    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, self.SSID_UUID,
                                ["read", "write"], service)
        self.value = []

    def ReadValue(self, options):
        logging.info('WiFi SSID: %s' % convert_array_to_str(self.value))
        return self.value
