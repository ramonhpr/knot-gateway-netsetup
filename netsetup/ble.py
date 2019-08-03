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
import gobject
from dbus.service import method as dbus_method

from srv_gatt_ot import OpenthreadService
from srv_gatt_wifi import WifiService
from ble_util.advertisement import Advertisement
from ble_util.application import Application
from ble_util.errors import InvalidArgsException
from ble_util.constants.dbus_interfaces import DBUS_OM_IFACE
from ble_util.constants.dbus_interfaces import BLUEZ_SERVICE_NAME
from ble_util.constants.dbus_interfaces import LE_ADVERTISING_MANAGER_IFACE
from ble_util.constants.dbus_interfaces import GATT_MANAGER_IFACE

logging.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s\n',
                    stream=sys.stderr, level=logging.INFO)

ADVERTISEMENT_TOGGLE_MS = 500


class KnotApplication(Application):
    def __init__(self, bus):
        global wpantun
        Application.__init__(self, bus)
        self.add_service(OpenthreadService(bus, 0, wpantun))
        self.add_service(WifiService(bus, 1))


class KnotAdvertisement(Advertisement):
    def __init__(self, bus, index, gatt_knot, ad_name):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.gatt_knot = gatt_knot
        self.add_service_uuid(gatt_knot.services[0].UUID)
        self.current_srv_gatt = 0
        self.add_local_name(ad_name)
        self.include_tx_power = True

    def toggle_uuid(self):
        counter_srv = len(self.gatt_knot.services)
        self.current_srv_gatt = (self.current_srv_gatt + 1) % counter_srv
        uuid = self.gatt_knot.services[self.current_srv_gatt].UUID
        self.service_uuids = []
        self.add_service_uuid(uuid)


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

    def __toggle_advertisement(self, on_error):
        self.ad_manager.UnregisterAdvertisement(
            self.ad_knot,
            reply_handler=lambda: None,
            error_handler=on_error)
        self.ad_knot.toggle_uuid()
        self.ad_manager.RegisterAdvertisement(
            self.ad_knot.get_path(), {},
            reply_handler=lambda: None,
            error_handler=on_error)
        return True  # return True to keep triggering timeout

    def register_advertisement(self, on_registered, on_error):
        def __on_register_ad():
            gobject.timeout_add(ADVERTISEMENT_TOGGLE_MS,
                                self.__toggle_advertisement, on_error)
            on_registered()

        self.ad_manager.RegisterAdvertisement(
            self.ad_knot.get_path(), {},
            reply_handler=__on_register_ad,
            error_handler=on_error)

    def register_gatt_app(self, on_registered, on_error):
        self.gatt_manager.RegisterApplication(
            self.gatt_knot.get_path(), {},
            reply_handler=on_registered,
            error_handler=on_error)

    def unregister_advertisement(self):
        self.ad_manager.UnregisterAdvertisement(self.ad_knot)

    def unregister_gatt_app(self):
        self.gatt_manager.UnregisterApplication(self.gatt_knot)


def find_adapter(bus, iface):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if iface in props.keys():
            return o

    return None
