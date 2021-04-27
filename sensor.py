# -*- coding: utf-8 -*-

class Sensor(object):

    """ Hue Sensor object

    Sensor config and state can be read and updated via the properties of this object

    """

    class State(dict):
        def __init__(self, sensor_bridge, sensor_id):
            self._bridge = sensor_bridge
            self._sensor_id = sensor_id

        def __setitem__(self, key, value):
            dict.__setitem__(self, key, value)
            self._bridge.set_sensor_state(self._sensor_id, self)

    class Config(dict):
        def __init__(self, sensor_bridge, sensor_id):
            self._bridge = sensor_bridge
            self._sensor_id = sensor_id

        def __setitem__(self, key, value):
            dict.__setitem__(self, key, value)
            self._bridge.set_sensor_config(self._sensor_id, self)

    class Bridge(object):

        def __init__(self, bridge):
            self.bridge = bridge
            self.sensors_by_id = {}
            self.sensors_by_name = {}

        def get_sensor_id_by_name(self, name):
            """ Lookup a sensor id based on string name. Case-sensitive. """
            sensors = self.get_sensor()
            for sensor_id in sensors:
                if name == sensors[sensor_id]['name']:
                    return sensor_id
            return False

        def get_sensor_objects(self, mode='list'):
            """Returns a collection containing the sensors, either by name or id (use 'id' or 'name' as the mode)
            The returned collection can be either a list (default), or a dict.
            Set mode='id' for a dict by sensor ID, or mode='name' for a dict by sensor name.   """
            if self.sensors_by_id == {}:
                sensors = self.bridge.get('/sensors/')
                for sensor in sensors:
                    self.sensors_by_id[int(sensor)] = Sensor(self, int(sensor))
                    self.sensors_by_name[sensors[sensor][
                        'name']] = self.sensors_by_id[int(sensor)]
            if mode == 'id':
                return self.sensors_by_id
            if mode == 'name':
                return self.sensors_by_name
            if mode == 'list':
                return self.sensors_by_id.values()

        @property
        def sensors(self):
            """ Access sensors as a list """
            return self.get_sensor_objects()

        def create_sensor(self, name, modelid, swversion, sensor_type, uniqueid, manufacturername, state={}, config={}, recycle=False):
            """ Create a new sensor in the bridge. Returns (ID,None) of the new sensor or (None,message) if creation failed. """
            data = {
                "name": name,
                "modelid": modelid,
                "swversion": swversion,
                "type": sensor_type,
                "uniqueid": uniqueid,
                "manufacturername": manufacturername,
                "recycle": recycle
            }
            if (isinstance(state, dict) and state != {}):
                data["state"] = state

            if (isinstance(config, dict) and config != {}):
                data["config"] = config

            result = self.bridge.post('/sensors/', data)

            if ("success" in result[0].keys()):
                new_id = result[0]["success"]["id"]
                logger.debug("Created sensor with ID " + new_id)
                new_sensor = Sensor(self, int(new_id))
                self.sensors_by_id[new_id] = new_sensor
                self.sensors_by_name[name] = new_sensor
                return new_id, None
            else:
                logger.debug("Failed to create sensor:" + repr(result[0]))
                return None, result[0]

        def get_sensor(self, sensor_id=None, parameter=None):
            """ Gets state by sensor_id and parameter"""

            if is_string(sensor_id):
                sensor_id = self.get_sensor_id_by_name(sensor_id)
            if sensor_id is None:
                return self.bridge.get('/sensors/')
            data = self.bridge.get('/sensors/' + str(sensor_id))

            if isinstance(data, list):
                logger.debug("Unable to read sensor with ID {0}: {1}".format(sensor_id, repr(data)))
                return None

            if parameter is None:
                return data
            return data[parameter]

        def set_sensor(self, sensor_id, parameter, value=None):
            """ Adjust properties of a sensor

            sensor_id must be a single sensor.
            parameters: 'name' : string

            """
            if isinstance(parameter, dict):
                data = parameter
            else:
                data = {parameter: value}

            result = None
            logger.debug(str(data))
            result = self.bridge.put('/sensors/' + str(
                sensor_id), data)
            if 'error' in list(result[0].keys()):
                logger.warn("ERROR: {0} for sensor {1}".format(
                    result[0]['error']['description'], sensor_id))

            logger.debug(result)
            return result

        def set_sensor_state(self, sensor_id, parameter, value=None):
            """ Adjust the "state" object of a sensor

            sensor_id must be a single sensor.
            parameters: any parameter(s) present in the sensor's "state" dictionary.

            """
            self.set_sensor_content(sensor_id, parameter, value, "state")

        def set_sensor_config(self, sensor_id, parameter, value=None):
            """ Adjust the "config" object of a sensor

            sensor_id must be a single sensor.
            parameters: any parameter(s) present in the sensor's "config" dictionary.

            """
            self.set_sensor_content(sensor_id, parameter, value, "config")

        def set_sensor_content(self, sensor_id, parameter, value=None, structure="state"):
            """ Adjust the "state" or "config" structures of a sensor
            """
            if (structure != "state" and structure != "config"):
                logger.debug("set_sensor_current expects structure 'state' or 'config'.")
                return False

            if isinstance(parameter, dict):
                data = parameter.copy()
            else:
                data = {parameter: value}

            # Attempting to set this causes an error.
            if "lastupdated" in data:
                del data["lastupdated"]

            result = None
            logger.debug(str(data))
            result = self.bridge.put('/sensors/' + str(
                sensor_id) + "/" + structure, data)
            if 'error' in list(result[0].keys()):
                logger.warn("ERROR: {0} for sensor {1}".format(
                    result[0]['error']['description'], sensor_id))

            logger.debug(result)
            return result

        def delete_sensor(self, sensor_id):
            try:
                name = self.sensors_by_id[sensor_id].name
                del self.sensors_by_name[name]
                del self.sensors_by_id[sensor_id]
                return self.bridge.delete('/sensors/' + str(sensor_id))
            except:
                logger.debug("Unable to delete nonexistent sensor with ID {0}".format(sensor_id))

    def __init__(self, sensor_bridge, sensor_id):
        self.bridge = sensor_bridge
        self.sensor_id = sensor_id

        self._name = None
        self._model = None
        self._swversion = None
        self._type = None
        self._uniqueid = None
        self._manufacturername = None
        self._state = Sensor.State(self.bridge, sensor_id)
        self._config = {}
        self._recycle = None

    def __repr__(self):
        # like default python repr function, but add sensor name
        return '<{0}.{1} object "{2}" at {3}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self)))

    # Wrapper functions for get/set through the bridge
    def _get(self, *args, **kwargs):
        return self.bridge.get_sensor(self.sensor_id, *args, **kwargs)

    def _set(self, *args, **kwargs):
        return self.bridge.set_sensor(self.sensor_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the sensor [string]'''
        return self._get('name')

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self._set('name', self._name)

        logger.debug("Renaming sensor from '{0}' to '{1}'".format(
            old_name, value))

        self.bridge.sensors_by_name[self.name] = self
        del self.bridge.sensors_by_name[old_name]

    @property
    def modelid(self):
        '''Get a unique identifier of the hardware model of this sensor [string]'''
        self._modelid = self._get('modelid')
        return self._modelid

    @property
    def swversion(self):
        '''Get the software version identifier of the sensor's firmware [string]'''
        self._swversion = self._get('swversion')
        return self._swversion

    @property
    def type(self):
        '''Get the sensor type of this device [string]'''
        self._type = self._get('type')
        return self._type

    @property
    def uniqueid(self):
        '''Get the unique device ID of this sensor [string]'''
        self._uniqueid = self._get('uniqueid')
        return self._uniqueid

    @property
    def manufacturername(self):
        '''Get the name of the manufacturer [string]'''
        self._manufacturername = self._get('manufacturername')
        return self._manufacturername

    @property
    def state(self):
        ''' A dictionary of sensor state. Some values can be updated, some are read-only. [dict]'''
        data = self._get('state')
        self._state.clear()
        self._state.update(data)
        return self._state

    @state.setter
    def state(self, data):
        self._state.clear()
        self._state.update(data)

    @property
    def config(self):
        ''' A dictionary of sensor config. Some values can be updated, some are read-only. [dict]'''
        data = self._get('config')
        self._config.clear()
        self._config.update(data)
        return self._config

    @config.setter
    def config(self, data):
        self._config.clear()
        self._config.update(data)

    @property
    def recycle(self):
        ''' True if this resource should be automatically removed when the last reference to it disappears [bool]'''
        self._recycle = self._get('manufacturername')
        return self._manufacturername
