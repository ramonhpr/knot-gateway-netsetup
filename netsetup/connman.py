import logging
import dbus
from dbus.exceptions import DBusException

CONNMAN_SERVICE_NAME = 'net.connman'
CONNMAN_MANAGER_INTERFACE = '%s.Manager' %CONNMAN_SERVICE_NAME
CONNMAN_TECHNOLOGY_INTERFACE = '%s.Technology' %CONNMAN_SERVICE_NAME

DEFAULT_SSID = 'knot_gw'
DEFAULT_PSW = 'knotNetworkOfThings'

class ConnmanClient(object):
    def __get_manager_interface(self):
        try:
            return dbus.Interface(
                self.bus.get_object(CONNMAN_SERVICE_NAME, '/'),
                                    CONNMAN_MANAGER_INTERFACE)
        except DBusException as err: # ignore if connmand is not running
            logging.error('%s: Connmand is not running. Unable to get interface manager' %err)
            return

    def __init__(self):
        self.bus = dbus.SystemBus()

        self.manager = self.__get_manager_interface()

    def __enable_wifi(self, iface):
        properties = iface.GetProperties()
        if not properties.get('Powered'):
            iface.SetProperty('Powered', dbus.Boolean(1))
            logging.info('Wifi enabled')


    def __get_wifi_technology_path(self):
        if not self.manager:
            logging.error('Unable to get wifi technology. Connman is not running')
            return

        for obj_path, properties in self.manager.GetTechnologies():
                if properties.get('Type') == 'wifi':
                        return obj_path

    def enable_tethering(self):
        path = self.__get_wifi_technology_path()

        if not path:
            logging.error('Not found technology wifi')
            return

        wifi_tech = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, path),
                           CONNMAN_TECHNOLOGY_INTERFACE)

        self.__enable_wifi(wifi_tech)
        try:
                wifi_tech.SetProperty('TetheringIdentifier',
                                      dbus.String(DEFAULT_SSID))
                wifi_tech.SetProperty('TetheringPassphrase',
                                      dbus.String(DEFAULT_PSW))
                wifi_tech.SetProperty('Tethering', dbus.Boolean(1))
                logging.info('Tethering enabled: SSID %s PSW: %s', DEFAULT_SSID,
                             DEFAULT_PSW)
        except DBusException as err:
                logging.error('DBus error')
                logging.error(err)
