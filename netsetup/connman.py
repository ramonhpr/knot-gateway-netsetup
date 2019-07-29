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


class ConnmanClient(object):
    def __init__(self):
        self.bus = dbus.SystemBus()

        self.manager = self.__get_manager_interface()

    def __get_manager_interface(self):
        try:
            return dbus.Interface(
                self.bus.get_object(CONNMAN_SERVICE_NAME, '/'),
                CONNMAN_MANAGER_INTERFACE)
        except DBusException as err:
            logging.error('%s: DBus Error, Connman is probably not \
                running.' % err)
            return
