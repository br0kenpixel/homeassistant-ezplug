from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_EDITABLE, CONF_ID
import pyezviz
import logging

_LOGGER = logging.getLogger(__name__)

class EZClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.client = pyezviz.client.EzvizClient(email, password)
        self.login()

    def login(self):
        try:
            self.token = self.client.login()
            return True
        except Exception as ex:
            raise Exception("Failed to log in -> " + str(ex))

    def logout(self):
        return self.client.logout()

    def getAllDevices(self):
        return self.client.get_device_infos()

    def getAllPlugs(self):
        devices = self.getAllDevices()
        smart_plugs = list()
        for device in devices.keys():
            if device[0] == "Q":
                smart_plugs.append(devices[device])
        return tuple(smart_plugs)

    def extractPlugState(self, plug_data):
        if not isinstance(plug_data, dict):
            raise ValueError("Expected dictionary with plug data")
        state_data = plug_data["SWITCH"]
        state_data = next((status_data["enable"] for status_data in state_data if status_data["type"] == 14), None)
        if state_data == None:
            raise Exception("Unable to find state")
        elif isinstance(state_data, bool):
            return state_data
        else:
            raise Exception("Unexpected state type \"%s\"" % type(state_data))

    def extractPlugOnlineState(self, plug_data):
          if not isinstance(plug_data, dict):
              raise ValueError("Expected dictionary with plug data")
          state_data = plug_data["STATUS"]["optionals"]["OnlineStatus"]
          return state_data == "1"

    def getPlug(self, **kwargs):
        smart_plugs = self.getAllPlugs()
        if "name" in kwargs.keys():
            identifier = "name"
        elif "deviceSerial" in kwargs.keys():
            identifier = "deviceSerial"
        elif "fullSerial" in kwargs.keys():
            identifier = "fullSerial"
        else:
            raise ValueError("Invalid filter type, use \"name\", \"deviceSerial\" or \"fullSerial\"")
        target_value = kwargs[identifier]

        get_prop = lambda dev, prop: dev["deviceInfos"][prop]
        result = None
        for device in smart_plugs:
            if get_prop(device, identifier) == target_value:
                result = device
                break
        if result is None:
            raise Exception("No devices found")
        else:
            return result

    def getPlugState(self, **kwargs):
        plug = self.getPlug(**kwargs)
        return self.extractPlugState(plug)

    def getPlugOnlineState(self, **kwargs):
        plug = self.getPlug(**kwargs)
        return self.extractPlugOnlineState(plug)

    def setPlugState(self, *args, **kwargs):
        if len(args) != 1 or len(kwargs.keys()) != 1:
            raise ValueError("Invalid arguments, expected [state/bool] [filter]")
        elif not isinstance(args[0], bool):
            raise ValueError("Invalid state, expected boolean")
        else:
            state = int(args[0])
            if "deviceSerial" not in kwargs.keys():
                plug = self.getPlug(**kwargs)
                serial = plug["deviceInfos"]["deviceSerial"]
            else:
                serial = kwargs["deviceSerial"]
            self.client.switch_status(serial, 14, state)

class SmartPlug(SwitchEntity):

    _attr_device_class = "switch"

    def __init__(self, name: str, serial: str, client: EZClient, uuid=None):
        self._name = name
        self.serial = serial
        self.client = client
        self._available = False
        self._editable = True
        self._unique_id = uuid
        self.just_updated = 0
        self.update()

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    @property
    def available(self):
        return self._available

    @property
    def state_attributes(self):
        return {ATTR_EDITABLE: self._editable}

    @property
    def unique_id(self):
        return self._unique_id

    def turn_on(self, **kwargs):
        self.client.setPlugState(True, deviceSerial=self.serial)
        self._is_on = True
        self.just_updated = 1

    def turn_off(self, **kwargs):
        self.client.setPlugState(False, deviceSerial=self.serial)
        self._is_on = False
        self.just_updated = 1

    def toggle(self, **kwargs):
        self.client.setPlugState(not self._is_on, deviceSerial=self.serial)
        self._is_on = not self._is_on

    def update(self):
        if self.just_updated == 1:
            self.just_updated = 0
            return
        self._available = self.client.getPlugOnlineState(deviceSerial=self.serial)
        self._is_on = self.client.getPlugState(deviceSerial=self.serial)

def setup_platform(hass, config, add_devices, discovery_info=None):
    email = config.get("email", None)
    password = config.get("password", None)
    if email == None or password == None:
        _LOGGER.error("Missing email, password configuration")
        return False
    _LOGGER.info(" === === === EZPlug === === ===")
    _LOGGER.info("Made by: br0kenpixel")
    client = EZClient(email, password)
    devs = client.getAllPlugs()
    for dev in devs:
        name = dev["deviceInfos"]["name"]
        serial = dev["deviceInfos"]["deviceSerial"]
        plug_t = SmartPlug(name, serial, client, config[CONF_ID])
        add_devices([plug_t])
    _LOGGER.info("EZPlug finished setup")
    return True
