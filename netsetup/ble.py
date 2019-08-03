#!/usr/bin/env python
#
# Copyright (c) 2019, CESAR. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import struct
import logging
import dbus
from dbus.service import method as dbus_method

from srv_gatt_ot import OpenthreadService
from ble_util.advertisement import Advertisement
from ble_util.application import Application
from ble_util.errors import InvalidArgsException
from ble_util.constants.dbus_interfaces import DBUS_OM_IFACE
from ble_util.constants.dbus_interfaces import BLUEZ_SERVICE_NAME
from ble_util.constants.dbus_interfaces import LE_ADVERTISING_MANAGER_IFACE
from ble_util.constants.dbus_interfaces import GATT_MANAGER_IFACE

logging.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s\n',
                    stream=sys.stderr, level=logging.INFO)

wpantun = None


class KnotApplication(Application):
    def __init__(self, bus):
        global wpantun
        Application.__init__(self, bus)
        self.add_service(OpenthreadService(bus, 0, wpantun))


class KnotAdvertisement(Advertisement):
    def __init__(self, bus, index, gatt_knot, ad_name):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.gatt_knot = gatt_knot
        self.add_service_uuid(gatt_knot.services[0].UUID)
        self.current_srv_gatt = 0
        self.add_local_name(ad_name)
        self.include_tx_power = True


class BleService(object):
    bus = None

    ad_adapter = None
    ad_adapter_props = None
    ad_manager = None
    ad_knot = None

    gatt_adapter = None
    gatt_manager = None
    gatt_knot = None

    def __init__(self, wpan, ad_name):
        global wpantun

        self.bus = dbus.SystemBus()
        wpantun = wpan

        self.ad_adapter = find_adapter(self.bus, LE_ADVERTISING_MANAGER_IFACE)
        if not self.ad_adapter:
            logging.error("LEAdvertiseManager1 interface not found")

        self.ad_adapter_props = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, self.ad_adapter),
            "org.freedesktop.DBus.Properties")

        self.ad_adapter_props.Set("org.bluez.Adapter1",
                                  "Powered", dbus.Boolean(1))

        self.ad_manager = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME,
                                self.ad_adapter),
            LE_ADVERTISING_MANAGER_IFACE)

        self.gatt_knot = KnotApplication(self.bus)

        self.ad_knot = KnotAdvertisement(self.bus, 0, self.gatt_knot, ad_name)

        self.gatt_adapter = find_adapter(self.bus, GATT_MANAGER_IFACE)
        if not self.gatt_adapter:
            logging.error("GattManager1 interface not found")

        self.gatt_manager = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, self.gatt_adapter),
            GATT_MANAGER_IFACE)


def find_adapter(bus, iface):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if iface in props.keys():
            return o

    return None
