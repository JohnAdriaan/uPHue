# -*- coding: utf-8 -*-

class Schedule(object):

    """ This is merely a container for `Schedule.Bridge`"""

    class Bridge(object):

        def __init__(self, bridge):
            self.bridge = bridge

        # Schedules #####
        def get_schedule(self, schedule_id=None, parameter=None):
            if schedule_id is None:
                return self.bridge.get('/schedules')
            if parameter is None:
                return self.bridge.get('/schedules/' + str(schedule_id))

        def create_schedule(self, name, time, light_id, data, description=' '):
            schedule = {
                'name': name,
                'localtime': time,
                'description': description,
                'command':
                {
                    'method': 'PUT',
                    'address': (self.bridge.api +
                                '/lights/' + str(light_id) + '/state'),
                    'body': data
                }
            }
            return self.bridge.post('/schedules', schedule)

        def set_schedule_attributes(self, schedule_id, attributes):
            """
            :param schedule_id: The ID of the schedule
            :param attributes: Dictionary with attributes and their new values
            """
            return self.bridge.put('/schedules/' + str(schedule_id), data=attributes)

        def create_group_schedule(self, name, time, group_id, data, description=' '):
            schedule = {
                'name': name,
                'localtime': time,
                'description': description,
                'command':
                {
                    'method': 'PUT',
                    'address': (self.bridge.api +
                                '/groups/' + str(group_id) + '/action'),
                    'body': data
                }
            }
            return self.bridge.post('/schedules', schedule)

        def delete_schedule(self, schedule_id):
            return self.bridge.delete('/schedules/' + str(schedule_id))
