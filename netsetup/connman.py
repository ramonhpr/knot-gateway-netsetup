import logging
import dbus
import gobject
from dbus.exceptions import DBusException

CONNMAN_SERVICE_NAME = 'net.connman'
CONNMAN_MANAGER_INTERFACE = '%s.Manager' %CONNMAN_SERVICE_NAME
CONNMAN_TECHNOLOGY_INTERFACE = '%s.Technology' %CONNMAN_SERVICE_NAME

SSID_PREFIX = 'knot_gw'
DEFAULT_PSW = 'knotNetworkOfThings'
SCAN_TIMEOUT_MS = 5000

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

    def __get_ethernet_service_properties(self):
        if not self.manager:
            logging.error('%s: unable to get ethernet technology. Connman is not running')
            return

        for obj_path, properties in self.manager.GetServices():
                if properties.get('Type') == 'ethernet':
                        return properties

    def __parse_mac_address(self, mac):
        return mac.replace(':', '_')

    def __get_mac_address(self):
        properties_ethernet = self.__get_ethernet_service_properties()
        mac = properties_ethernet.get('Ethernet').get('Address')
        return self.__parse_mac_address(mac)

    def enable_tethering(self):
        path = self.__get_wifi_technology_path()

        if not path:
            logging.error('Not found technology wifi')
            return

        wifi_tech = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, path),
                           CONNMAN_TECHNOLOGY_INTERFACE)

        mac = self.__get_mac_address()
        ssid = '%s_%s' %(SSID_PREFIX, mac)

        self.__enable_wifi(wifi_tech)
        try:
                wifi_tech.SetProperty('TetheringIdentifier',
                                      dbus.String(ssid))
                wifi_tech.SetProperty('TetheringPassphrase',
                                      dbus.String(DEFAULT_PSW))
                wifi_tech.SetProperty('Tethering', dbus.Boolean(True))
                logging.info('Tethering enabled: SSID %s PSW: %s', ssid,                     DEFAULT_PSW)
        except DBusException as err:
                logging.error('DBus error')
                logging.error(err)

    def get_wifi_services(self):
        if not self.manager:
            logging.error('Unable to get wifi services. Connman is not running')
            return

        services = self.manager.GetServices()

        return [properties for obj_path, properties in services if                      properties.get('Type') == 'wifi']


    def disable_tethering(self):
        path = self.__get_wifi_technology_path()

        if not path:
            logging.error('Not found technology wifi')
            return

        wifi_tech = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, path),
                           CONNMAN_TECHNOLOGY_INTERFACE)

        try:
                wifi_tech.SetProperty('Tethering', dbus.Boolean(False))
                logging.info('Tethering disabled')
        except DBusException as err:
                logging.error('DBus error')
                logging.error(err)

    def scan_wifi(self, onServicesDiscovered):
        path = self.__get_wifi_technology_path()

        if not path:
            logging.error('Not found technology wifi')
            return

        wifi_tech = dbus.Interface(
            self.bus.get_object(CONNMAN_SERVICE_NAME, path),
                           CONNMAN_TECHNOLOGY_INTERFACE)


        self.disable_tethering()

        # Wait until the property be set
        def on_tethering_changed():
            signal_match.remove()
            wifi_tech.Scan()

        signal_match = self.bus.add_signal_receiver(on_tethering_changed, 'PropertiesChanged', CONNMAN_TECHNOLOGY_INTERFACE, path=path)

        self.signal_match = self.manager.connect_to_signal('ServicesChanged', lambda x, y: logging.info(x + y))

        def on_scanned():
            logging.info('Scan completed')
            self.signal_match.remove()
        gobject.timeout_add(SCAN_TIMEOUT_MS, on_scanned)
