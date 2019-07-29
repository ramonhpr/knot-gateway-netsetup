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
