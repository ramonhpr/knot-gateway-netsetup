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

logging.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s\n',
                    stream=sys.stderr, level=logging.INFO)


BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE = 'org.bluez.GattDescriptor1'

LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'


wpantun = None


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus_method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        logging.info('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation
    """
    PATH_BASE = '/org/bluez/knot/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus_method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    self.get_descriptor_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus_method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus_method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        logging.info('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus_method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        logging.info('Default WriteValue called, returning error')
        raise NotSupportedException()

    @dbus_method(GATT_CHRC_IFACE)
    def StartNotify(self):
        logging.info('Default StartNotify called, returning error')
        raise NotSupportedException()

    @dbus_method(GATT_CHRC_IFACE)
    def StopNotify(self):
        logging.info('Default StopNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class KnotApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(OpenthreadService(bus, 0))


class OpenthreadService(Service):
    OT_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900e30"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.OT_UUID, True)
        self.add_characteristic(OpenthreadChannelCharacteristic(bus, 0, self))
        self.add_characteristic(OpenthreadNameCharacteristic(bus, 1, self))
        self.add_characteristic(OpenthreadPanIDCharacteristic(bus, 2, self))
        self.add_characteristic(OpenthreadXPanIDCharacteristic(bus, 3, self))
        self.add_characteristic(OpenthreadMasterKeyCharacteristic(bus, 4,
                                                                  self))
        self.add_characteristic(OpenthreadStateCharacteristic(bus, 5, self))
        self.add_characteristic(OpenthreadMeshIPv6Characteristic(bus, 6, self))


class OpenthreadChannelCharacteristic(Characteristic):
    CHANNEL_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d31"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.CHANNEL_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in struct.pack(">l", wpantun.channel))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadChannelCharacteristic Read: ' +
                     repr(self.value))
        return self.value


class OpenthreadNameCharacteristic(Characteristic):
    NAME_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d32"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.NAME_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in bytes(wpantun.network_name))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadNameCharacteristic Read: ' + repr(self.value))
        return self.value


class OpenthreadPanIDCharacteristic(Characteristic):
    PANID_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d33"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.PANID_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in struct.pack(">H", wpantun.pan_id))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadPanIDCharacteristic Read: ' + repr(self.value))
        return self.value


class OpenthreadXPanIDCharacteristic(Characteristic):
    XPANID_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d34"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.XPANID_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in struct.pack(">Q", wpantun.xpan_id))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadXPanIDCharacteristic Read: ' +
                     repr(self.value))
        return self.value


class OpenthreadMasterKeyCharacteristic(Characteristic):
    MASTERKEY_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d35"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.MASTERKEY_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in bytes(wpantun.masterkey))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadMasterKeyCharacteristic Read: ' +
                     repr(self.value))
        return self.value


class OpenthreadStateCharacteristic(Characteristic):
    STATE_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d36"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.STATE_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in bytes(wpantun.state))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadStateCharacteristic Read: ' + repr(self.value))
        return self.value


class OpenthreadMeshIPv6Characteristic(Characteristic):
    MESHIPV6_CHRC_UUID = "a8a9e49c-aa9a-d441-9bec-817bb4900d37"

    def __init__(self, bus, index, service):
        global wpantun
        Characteristic.__init__(self, bus, index, self.MESHIPV6_CHRC_UUID,
                                ["read"], service)
        if wpantun is not None:
            self.value = dbus.Array(
                dbus.Byte(i) for i in bytes(wpantun.mesh_ipv6))
        else:
            self.value = []

    def ReadValue(self, options):
        logging.info('OpenthreadMeshIPv6Characteristic Read: ' +
                     repr(self.value))
        return self.value


class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/knot/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = None
        self.include_tx_power = None
        self.data = None
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.include_tx_power is not None:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)

        if self.data is not None:
            properties['Data'] = dbus.Dictionary(
                self.data, signature='yv')
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = dbus.Dictionary({}, signature='qv')
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = dbus.Dictionary({}, signature='sv')
        self.service_data[uuid] = dbus.Array(data, signature='y')

    def add_local_name(self, name):
        if not self.local_name:
            self.local_name = ""
        self.local_name = dbus.String(name)

    def add_data(self, ad_type, data):
        if not self.data:
            self.data = dbus.Dictionary({}, signature='yv')
        self.data[ad_type] = dbus.Array(data, signature='y')

    @dbus_method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        logging.info('GetAll')
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        logging.info('returning props')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus_method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        logging.info('%s: Released!' % self.path)


class KnotAdvertisement(Advertisement):
    def __init__(self, bus, index, ad_name):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid("a8a9e49c-aa9a-d441-9bec-817bb4900e30")
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

        self.ad_knot = KnotAdvertisement(self.bus, 0, ad_name)

        self.gatt_adapter = find_adapter(self.bus, GATT_MANAGER_IFACE)
        if not self.gatt_adapter:
            logging.error("GattManager1 interface not found")

        self.gatt_manager = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, self.gatt_adapter),
            GATT_MANAGER_IFACE)

        self.gatt_knot = KnotApplication(self.bus)


def find_adapter(bus, iface):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if iface in props.keys():
            return o

    return None
