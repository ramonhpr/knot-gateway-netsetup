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
CONNMAN_SERVICE_INTERFACE = '%s.Service' % CONNMAN_SERVICE_NAME
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
    def __get_manager_interface(self):
        try:
            return dbus.Interface(
                self.bus.get_object(CONNMAN_SERVICE_NAME, '/'),
                CONNMAN_MANAGER_INTERFACE)
        except DBusException as err:  # ignore if connmand is not running
            logging.error('%s: Connman is probably not running.' % err)
            return

    def __init__(self):
        self.bus = dbus.SystemBus()

        self.manager = self.__get_manager_interface()
        self.agent = WifiAgent(self.bus, WIFI_AGENT_PATH)
        self.manager.RegisterAgent(WIFI_AGENT_PATH)

    def __enable_wifi(self, iface):
        properties = iface.GetProperties()
        if not properties.get('Powered'):
            iface.SetProperty('Powered', dbus.Boolean(True))
            logging.info('Wifi enabled')

    def __get_wifi_technology_path(self):
        if not self.manager:
            logging.error('Unable to get wifi technology. Connman not running')
            return

        for obj_path, properties in self.manager.GetTechnologies():
                if properties.get('Type') == 'wifi':
                        return obj_path

    def __scan_wifi(self, on_scan_completed):
        if not self.manager:
            logging.error('Unable to connect to wifi service')
            return []
        path = self.__get_wifi_technology_path()
        services = []

        if not path:
            logging.error('Not found technology wifi')
            return

        wifi_tech = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, path),
            CONNMAN_TECHNOLOGY_INTERFACE)

        self.__enable_wifi(wifi_tech)

        def on_services_changed(currentServices, rmServices):
            self.signal_match.remove()
            on_scan_completed(currentServices)
        self.signal_match = self.manager.connect_to_signal(
            'ServicesChanged', on_services_changed)

        wifi_tech.Scan(reply_handler=lambda: logging.info('Scan complete'),
                       error_handler=lambda err: logging.error(err))

    def __get_wifi_service_path(self, name):
        if not self.manager:
            logging.error('Unable to get wifi technology. Connman not running')
            return

        for obj_path, properties in self.manager.GetServices():
                if properties.get('Name') == name:
                        return obj_path

    def __do_connect(self, path):
        logging.info(path)
        service = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, path),
            CONNMAN_SERVICE_INTERFACE)

        service.Connect(reply_handler=lambda: logging.info('Connected'),
                        error_handler=lambda err: logging.error(err))

    def connect_wifi(self, name, password):
        self.agent.name = name
        self.agent.passphrase = password

        self.__scan_wifi(lambda services: self.__do_connect(
                       self.__get_wifi_service_path(name)))
