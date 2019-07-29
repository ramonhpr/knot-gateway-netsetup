#!/usr/bin/env python
#
# Copyright (c) 2019, CESAR. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

import logging
import dbus
from dbus.exceptions import DBusException

CONNMAN_SERVICE_NAME = 'net.connman'
CONNMAN_MANAGER_INTERFACE = '%s.Manager' % CONNMAN_SERVICE_NAME
CONNMAN_TECHNOLOGY_INTERFACE = '%s.Technology' % CONNMAN_SERVICE_NAME
CONNMAN_AGENT_INTERFACE = '%s.Agent' % CONNMAN_SERVICE_NAME

WIFI_AGENT_PATH = '/knot/netsetup/wifi/agent'


class WifiAgent(dbus.service.Object):
    @dbus.service.method(CONNMAN_AGENT_INTERFACE,
                         in_signature='', out_signature='')
    def Release(self):
        logging.info('release')

    @dbus.service.method(CONNMAN_AGENT_INTERFACE,
                         in_signature='', out_signature='')
    def Cancel(self):
        logging.info('cancel')

    @dbus.service.method(CONNMAN_AGENT_INTERFACE,
                         in_signature='oa{sv}',
                         out_signature='a{sv}')
    def RequestInput(self, path, fields):
        response = {}
        if 'Passphrase' in fields:
            response.update({'Passphrase': self.passphrase})

        logging.info('returning %s' % str(response))
        return response


class ConnmanClient(object):
    def __init__(self):
        self.bus = dbus.SystemBus()

        self.manager = self.__get_manager_interface()
        if not self.manager:
            logging.error('Unable to get connman manager. Probably \
                Connman is not running')
            return

        self.agent = WifiAgent(self.bus, WIFI_AGENT_PATH)
        self.manager.RegisterAgent(WIFI_AGENT_PATH)

    def __get_manager_interface(self):
        try:
            return dbus.Interface(
                self.bus.get_object(CONNMAN_SERVICE_NAME, '/'),
                CONNMAN_MANAGER_INTERFACE)
        except DBusException as err:
            logging.error('%s: DBus Error, Connman is probably not \
                running.' % err)
            return

    def __enable_wifi(self, iface):
        properties = iface.GetProperties()
        if not properties.get('Powered'):
            iface.SetProperty('Powered', dbus.Boolean(True))
            logging.info('Enabling wifi')

    def __get_wifi_technology(self):
        if not self.manager:
            logging.error('Unable to get wifi technology. Connman not running')
            return

        for obj_path, properties in self.manager.GetTechnologies():
                if properties.get('Type') == 'wifi':
                        break

        if properties.get('Type') != 'wifi':
            logging.error('Not found technology wifi')
            return

        wifi_tech_iface = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, obj_path),
            CONNMAN_TECHNOLOGY_INTERFACE)

        return wifi_tech_iface

    def __scan_wifi(self, on_scan_completed):
        if not self.manager:
            logging.error('Unable to connect to wifi service')
            return []

        wifi_tech = self.__get_wifi_technology()
        if not wifi_tech:
            logging.error('Not found technology wifi')
            return

        services = []

        self.__enable_wifi(wifi_tech)

        def on_services_changed(currentServices, rmServices):
            self.signal_match.remove()
            on_scan_completed(currentServices)

        self.signal_match = self.manager.connect_to_signal(
            'ServicesChanged', on_services_changed)

        wifi_tech.Scan(reply_handler=lambda: logging.info('Scan complete'),
                       error_handler=lambda err: logging.error(err))
