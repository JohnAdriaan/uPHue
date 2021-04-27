# -*- coding: utf-8 -*-

import light


class Group(light.Light):

    """ A group of Hue lights, tracked as a group on the bridge

    Example:

        >>> b = Bridge()
        >>> g1 = Group(b, 1)
        >>> g1.hue = 50000 # all lights in that group turn blue
        >>> g1.on = False # all will turn off

        >>> g2 = Group(b, 'Kitchen')  # you can also look up groups by name
        >>> # will raise a LookupError if the name doesn't match

    """

    class Bridge(Light.Bridge):

        def __init__(self, bridge):
            Light.Bridge.__init__(self, bridge)

        @property
        def groups(self):
            """ Access groups as a list """
            return [Group(self, int(groupid)) for groupid in self.get_group().keys()]

        def get_group_id_by_name(self, name):
            """ Lookup a group id based on string name. Case-sensitive. """
            groups = self.get_group()
            for group_id in groups:
                if name == groups[group_id]['name']:
                    return int(group_id)
            return False

        def get_group(self, group_id=None, parameter=None):
            if is_string(group_id):
                group_id = self.get_group_id_by_name(group_id)
            if group_id is False:
                logger.error('Group name does not exist')
                return
            if group_id is None:
                return self.bridge.get('/groups/')
            if parameter is None:
                return self.bridge.get('/groups/' + str(group_id))
            elif parameter == 'name' or parameter == 'lights':
                return self.bridge.get('/groups/' + str(group_id))[parameter]
            else:
                return self.bridge.get('/groups/' + str(group_id))['action'][parameter]

        def set_group(self, group_id, parameter, value=None, transitiontime=None):
            """ Change light settings for a group

            group_id : int, id number for group
            parameter : 'name' or 'lights'
            value: string, or list of light IDs if you're setting the lights

            """

            if isinstance(parameter, dict):
                data = parameter
            elif parameter == 'lights' and (isinstance(value, list) or isinstance(value, int)):
                if isinstance(value, int):
                    value = [value]
                data = {parameter: [str(x) for x in value]}
            else:
                data = {parameter: value}

            if transitiontime is not None:
                data['transitiontime'] = int(round(
                    transitiontime))  # must be int for request format

            group_id_array = group_id
            if isinstance(group_id, int) or is_string(group_id):
                group_id_array = [group_id]
            result = []
            for group in group_id_array:
                logger.debug(str(data))
                if is_string(group):
                    converted_group = self.get_group_id_by_name(group)
                else:
                    converted_group = group
                if converted_group is False:
                    logger.error('Group name does not exist')
                    return
                if parameter == 'name' or parameter == 'lights':
                    result.append(self.bridge.put('/groups/' + str(converted_group), data))
                else:
                    result.append(self.bridge.put('/groups/' + str(converted_group) + '/action', data))

            if 'error' in list(result[-1][0].keys()):
                logger.warn("ERROR: {0} for group {1}".format(
                    result[-1][0]['error']['description'], group))

            logger.debug(result)
            return result

        def create_group(self, name, lights=None):
            """ Create a group of lights

            Parameters
            ------------
            name : string
                Name for this group of lights
            lights : list
                List of lights to be in the group.

            """
            data = {'lights': [str(x) for x in lights], 'name': name}
            return self.bridge.post('/groups/', data)

        def delete_group(self, group_id):
            return self.bridge.delete('/groups/' + str(group_id))

    def __init__(self, group_bridge, group_id):
        Light.__init__(self, group_bridge, None)
        del self.light_id  # not relevant for a group

        try:
            self.group_id = int(group_id)
        except:
            name = group_id
            groups = self.bridge.get_group()
            for idnumber, info in groups.items():
                if info['name'] == name:
                    self.group_id = int(idnumber)
                    break
            else:
                raise LookupError("Could not find a group by that name.")

    # Wrapper functions for get/set through the bridge, adding support for
    # remembering the transitiontime parameter if the user has set it
    def _get(self, *args, **kwargs):
        return self.bridge.get_group(self.group_id, *args, **kwargs)

    def _set(self, *args, **kwargs):
        # let's get basic group functionality working first before adding
        # transition time...
        if self.transitiontime is not None:
            kwargs['transitiontime'] = self.transitiontime
            logger.debug("Setting with transitiontime = {0} ds = {1} s".format(
                self.transitiontime, float(self.transitiontime) / 10))

            if (args[0] == 'on' and args[1] is False) or (
                    kwargs.get('on', True) is False):
                self._reset_bri_after_on = True
        return self.bridge.set_group(self.group_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the light group [string]'''
        return self._get('name')

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        logger.debug("Renaming light group from '{0}' to '{1}'".format(
            old_name, value))
        self._set('name', self._name)

    @property
    def lights(self):
        """ Return a list of all lights in this group"""
        # response = self.bridge.request('GET', '/api/{0}/groups/{1}'.format(self.bridge.username, self.group_id))
        # return [Light(self.bridge, int(l)) for l in response['lights']]
        return [Light(self.bridge, int(l)) for l in self._get('lights')]

    @lights.setter
    def lights(self, value):
        """ Change the lights that are in this group"""
        logger.debug("Setting lights in group {0} to {1}".format(
            self.group_id, str(value)))
        self._set('lights', value)


class AllLights(Group):

    """ All the Hue lights connected to your bridge

    This makes use of the semi-documented feature that
    "Group 0" of lights appears to be a group automatically
    consisting of all lights.  This is not returned by
    listing the groups, but is accessible if you explicitly
    ask for group 0.
    """
    def __init__(self, bridge):
        Group.__init__(self, bridge, 0)
