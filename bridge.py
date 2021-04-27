# -*- coding: utf-8 -*-

import os
import socket
import json
import http.client as httplib

from uPHue import *


class Bridge(object):

    """ Interface to the Hue ZigBee bridge

    """
    def __init__(self, ip=None, username=None, config_file_path=None):
        """ Initialization function.

        Parameters:
        ------------
        ip : string
            IP address as dotted quad
        username : string, optional

        """

        if config_file_path is not None:
            self.config_file_path = config_file_path
        else:
            self.config_file_path = os.path.join(os.getcwd(), '.python_hue')

        self.ip = ip
        self.username = username
        if username is not None:
            self.api = '/api/' + username
        self._name = None

        # self.minutes = 600 # these do not seem to be used anywhere?
        # self.seconds = 10

        self.connect()

    @property
    def name(self):
        '''Get or set the name of the bridge [string]'''
        self._name = self.get('/config')['name']
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        data = {'name': self._name}
        self.put('/config', data)

    def get(self, req):
        return self.request('GET', self.api + req)

    def put(self, req, data):
        return self.request('PUT', self.api + req, data)

    def post(self, req, data):
        return self.request('POST', self.api + req, data)

    def delete(self, req):
        return self.request('DELETE', self.api + req)

    def request(self, mode='GET', address=None, data=None):
        """ Utility function for HTTP GET/PUT requests for the API"""
        connection = httplib.HTTPConnection(self.ip, timeout=10)

        try:
            if mode == 'GET' or mode == 'DELETE':
                connection.request(mode, address)
            if mode == 'PUT' or mode == 'POST':
                connection.request(mode, address, json.dumps(data))

            logger.debug("{0} {1} {2}".format(mode, address, str(data)))

        except socket.timeout:
            error = "{} Request to {}{} timed out.".format(mode, self.ip, address)

            logger.exception(error)
            raise PhueRequestTimeout(None, error)

        result = connection.getresponse()
        response = result.read()
        connection.close()
        response = response.decode('utf-8')

        logger.debug(response)
        return json.loads(response)

    def get_ip_address(self, set_result=False):

        """ Get the bridge ip address from the meethue.com nupnp api """

        connection = httplib.HTTPSConnection('www.meethue.com')
        connection.request('GET', '/api/nupnp')

        logger.info('Connecting to meethue.com/api/nupnp')

        result = connection.getresponse()

        data = json.loads(str(result.read(), encoding='utf-8'))

        """ close connection after read() is done, to prevent issues with read() """

        connection.close()

        ip = str(data[0]['internalipaddress'])

        if ip != '':
            if set_result:
                self.ip = ip

            return ip
        else:
            return False

    def register_app(self):
        """ Register this computer with the Hue bridge hardware and save the resulting access token """
        registration_request = {"devicetype": "python_hue"}
        response = self.request('POST', '/api', registration_request)
        for line in response:
            for key in line:
                if 'success' in key:
                    with open(self.config_file_path, 'w') as f:
                        logger.info(
                            'Writing configuration file to ' + self.config_file_path)
                        f.write(json.dumps({self.ip: line['success']}))
                        logger.info('Reconnecting to the bridge')
                    self.connect()
                if 'error' in key:
                    error_type = line['error']['type']
                    if error_type == 101:
                        raise PhueRegistrationException(error_type,
                                                        'The link button has not been pressed in the last 30 seconds.')
                    if error_type == 7:
                        raise PhueException(error_type,
                                            'Unknown username')

    def connect(self):
        """ Connect to the Hue bridge """
        logger.info('Attempting to connect to the bridge...')
        # If the ip and username were provided at class init
        if self.ip is not None and self.username is not None:
            logger.info('Using ip: ' + self.ip)
            logger.info('Using username: ' + self.username)
            return

        if self.ip is None or self.username is None:
            try:
                with open(self.config_file_path) as f:
                    config = json.loads(f.read())
                    if self.ip is None:
                        self.ip = list(config.keys())[0]
                        logger.info('Using ip from config: ' + self.ip)
                    else:
                        logger.info('Using ip: ' + self.ip)
                    if self.username is None:
                        self.username = config[self.ip]['username']
                        self.api = '/api/' + self.username
                        logger.info(
                            'Using username from config: ' + self.username)
                    else:
                        logger.info('Using username: ' + self.username)
            except Exception as e:
                logger.info(
                    'Error opening config file, will attempt bridge registration')
                self.register_app()

    def get_api(self):
        """ Returns the full api dictionary """
        return self.get('')
