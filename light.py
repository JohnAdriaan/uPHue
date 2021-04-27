# -*- coding: utf-8 -*-

from uPHue import *


class Light(object):

    """ Hue Light object

    Light settings can be accessed or set via the properties of this object.

    """

    class Bridge(object):

        """
            You can obtain Light objects by calling the get_light_objects method:

            >>> b = bridge.Bridge(ip='192.168.1.100')
            >>> lb = light.Light.Bridge(b)
            >>> lb.get_light_objects()
            [<phue.Light at 0x10473d750>,
             <phue.Light at 0x1046ce110>]

            Or more succinctly just by accessing this Bridge object as a list or dict:

            >>> lb[1]
            <phue.Light at 0x10473d750>
            >>> lb['Kitchen']
            <phue.Light at 0x10473d750>
        """

        def __init__(self, bridge):
            self.bridge = bridge
            self.lights_by_id = {}
            self.lights_by_name = {}

        def get_light_id_by_name(self, name):
            """ Lookup a light id based on string name. Case-sensitive. """
            lights = self.get_light()
            for light_id in lights:
                if name == lights[light_id]['name']:
                    return light_id
            return False

        def get_light_objects(self, mode='list'):
            """Returns a collection containing the lights, either by name or id (use 'id' or 'name' as the mode)
            The returned collection can be either a list (default), or a dict.
            Set mode='id' for a dict by light ID, or mode='name' for a dict by light name.   """
            if self.lights_by_id == {}:
                lights = self.bridge.get('/lights/')
                for light in lights:
                    self.lights_by_id[int(light)] = Light(self, int(light))
                    self.lights_by_name[lights[light][
                        'name']] = self.lights_by_id[int(light)]
            if mode == 'id':
                return self.lights_by_id
            if mode == 'name':
                return self.lights_by_name
            if mode == 'list':
                # return lights in sorted id order, dicts have no natural order
                return [self.lights_by_id[id] for id in sorted(self.lights_by_id)]

        def __getitem__(self, key):
            """ Lights are accessibly by indexing the bridge either with
            an integer index or string name. """
            if self.lights_by_id == {}:
                self.get_light_objects()

            try:
                return self.lights_by_id[key]
            except:
                try:
                    return self.lights_by_name[key]
                except:
                    raise KeyError(
                        'Not a valid key (integer index starting with 1, or light name): ' + str(key))

        @property
        def lights(self):
            """ Access lights as a list """
            return self.get_light_objects()

        def get_light(self, light_id=None, parameter=None):
            """ Gets state by light_id and parameter"""

            if is_string(light_id):
                light_id = self.get_light_id_by_name(light_id)
            if light_id is None:
                return self.bridge.get('/lights/')
            state = self.bridge.get('/lights/' + str(light_id))
            if parameter is None:
                return state
            if parameter in ['name', 'type', 'uniqueid', 'swversion']:
                return state[parameter]
            else:
                try:
                    return state['state'][parameter]
                except KeyError as e:
                    raise KeyError(
                        'Not a valid key, parameter %s is not associated with light %s)'
                        % (parameter, light_id))

        def set_light(self, light_id, parameter, value=None, transitiontime=None):
            """ Adjust properties of one or more lights.

            light_id can be a single lamp or an array of lamps
            parameters: 'on' : True|False , 'bri' : 0-254, 'sat' : 0-254, 'ct': 154-500

            transitiontime : in **deciseconds**, time for this transition to take place
                             Note that transitiontime only applies to *this* light
                             command, it is not saved as a setting for use in the future!
                             Use the Light class' transitiontime attribute if you want
                             persistent time settings.

            """
            if isinstance(parameter, dict):
                data = parameter
            else:
                data = {parameter: value}

            if transitiontime is not None:
                data['transitiontime'] = int(round(
                    transitiontime))  # must be int for request format

            light_id_array = light_id
            if isinstance(light_id, int) or is_string(light_id):
                light_id_array = [light_id]
            result = []
            for light in light_id_array:
                logger.debug(str(data))
                if parameter == 'name':
                    result.append(self.bridge.put('/lights/' + str(
                        light_id), data))
                else:
                    if is_string(light):
                        converted_light = self.get_light_id_by_name(light)
                    else:
                        converted_light = light
                    result.append(self.bridge.put('/lights/' + str(
                        converted_light) + '/state', data))
                if 'error' in list(result[-1][0].keys()):
                    logger.warn("ERROR: {0} for light {1}".format(
                        result[-1][0]['error']['description'], light))

            logger.debug(result)
            return result

    def __init__(self, light_bridge, light_id):
        self.bridge = light_bridge
        self.light_id = light_id

        self._name = None
        self._on = None
        self._brightness = None
        self._colormode = None
        self._hue = None
        self._saturation = None
        self._xy = None
        self._colortemp = None
        self._effect = None
        self._alert = None
        self.transitiontime = None  # default
        self._reset_bri_after_on = None
        self._reachable = None
        self._type = None

    def __repr__(self):
        # like default python repr function, but add light name
        return '<{0}.{1} object "{2}" at {3}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self)))

    # Wrapper functions for get/set through the bridge, adding support for
    # remembering the transitiontime parameter if the user has set it
    def _get(self, *args, **kwargs):
        return self.bridge.get_light(self.light_id, *args, **kwargs)

    def _set(self, *args, **kwargs):

        if self.transitiontime is not None:
            kwargs['transitiontime'] = self.transitiontime
            logger.debug("Setting with transitiontime = {0} ds = {1} s".format(
                self.transitiontime, float(self.transitiontime) / 10))

            if (args[0] == 'on' and args[1] is False) or (
                    kwargs.get('on', True) is False):
                self._reset_bri_after_on = True
        return self.bridge.set_light(self.light_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the light [string]'''
        return self._get('name')

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self._set('name', self._name)

        logger.debug("Renaming light from '{0}' to '{1}'".format(
            old_name, value))

        self.bridge.lights_by_name[self.name] = self
        del self.bridge.lights_by_name[old_name]

    @property
    def on(self):
        '''Get or set the state of the light [True|False]'''
        self._on = self._get('on')
        return self._on

    @on.setter
    def on(self, value):

        # Some added code here to work around known bug where
        # turning off with transitiontime set makes it restart on brightness = 1
        # see
        # http://www.everyhue.com/vanilla/discussion/204/bug-with-brightness-when-requesting-ontrue-transitiontime5

        # if we're turning off, save whether this bug in the hardware has been
        # invoked
        if self._on and value is False:
            self._reset_bri_after_on = self.transitiontime is not None
            if self._reset_bri_after_on:
                logger.warning(
                    'Turned off light with transitiontime specified, brightness will be reset on power on')

        self._set('on', value)

        # work around bug by resetting brightness after a power on
        if self._on is False and value is True:
            if self._reset_bri_after_on:
                logger.warning(
                    'Light was turned off with transitiontime specified, brightness needs to be reset now.')
                self.brightness = self._brightness
                self._reset_bri_after_on = False

        self._on = value

    @property
    def colormode(self):
        '''Get the color mode of the light [hs|xy|ct]'''
        self._colormode = self._get('colormode')
        return self._colormode

    @property
    def brightness(self):
        '''Get or set the brightness of the light [0-254].

        0 is not off'''

        self._brightness = self._get('bri')
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value
        self._set('bri', self._brightness)

    @property
    def hue(self):
        '''Get or set the hue of the light [0-65535]'''
        self._hue = self._get('hue')
        return self._hue

    @hue.setter
    def hue(self, value):
        self._hue = int(value)
        self._set('hue', self._hue)

    @property
    def saturation(self):
        '''Get or set the saturation of the light [0-254]

        0 = white
        254 = most saturated
        '''
        self._saturation = self._get('sat')
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._saturation = value
        self._set('sat', self._saturation)

    @property
    def xy(self):
        '''Get or set the color coordinates of the light [ [0.0-1.0, 0.0-1.0] ]

        This is in a color space similar to CIE 1931 (but not quite identical)
        '''
        self._xy = self._get('xy')
        return self._xy

    @xy.setter
    def xy(self, value):
        self._xy = value
        self._set('xy', self._xy)

    @property
    def colortemp(self):
        '''Get or set the color temperature of the light, in units of mireds [154-500]'''
        self._colortemp = self._get('ct')
        return self._colortemp

    @colortemp.setter
    def colortemp(self, value):
        if value < 154:
            logger.warn('154 mireds is coolest allowed color temp')
        elif value > 500:
            logger.warn('500 mireds is warmest allowed color temp')
        self._colortemp = value
        self._set('ct', self._colortemp)

    @property
    def colortemp_k(self):
        '''Get or set the color temperature of the light, in units of Kelvin [2000-6500]'''
        self._colortemp = self._get('ct')
        return int(round(1e6 / self._colortemp))

    @colortemp_k.setter
    def colortemp_k(self, value):
        if value > 6500:
            logger.warn('6500 K is max allowed color temp')
            value = 6500
        elif value < 2000:
            logger.warn('2000 K is min allowed color temp')
            value = 2000

        colortemp_mireds = int(round(1e6 / value))
        logger.debug("{0:d} K is {1} mireds".format(value, colortemp_mireds))
        self.colortemp = colortemp_mireds

    @property
    def effect(self):
        '''Check the effect setting of the light. [none|colorloop]'''
        self._effect = self._get('effect')
        return self._effect

    @effect.setter
    def effect(self, value):
        self._effect = value
        self._set('effect', self._effect)

    @property
    def alert(self):
        '''Get or set the alert state of the light [select|lselect|none]'''
        self._alert = self._get('alert')
        return self._alert

    @alert.setter
    def alert(self, value):
        if value is None:
            value = 'none'
        self._alert = value
        self._set('alert', self._alert)

    @property
    def reachable(self):
        '''Get the reachable state of the light [boolean]'''
        self._reachable = self._get('reachable')
        return self._reachable

    @property
    def type(self):
        '''Get the type of the light [string]'''
        self._type = self._get('type')
        return self._type
