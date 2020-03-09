# -----------------------------------------------------------------------
# Copyright (C) 2015-2020 King County Library System
# Bill Erickson <berickxx@gmail.com>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# -----------------------------------------------------------------------
import sys, logging, urllib3, re, json
from urllib.parse import urlencode, quote
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.message import Message, FixedField, Field
from pysip2.ils import IlsMod

institution = 'evergreen'
GATEWAY_PATH = '/osrf-gateway-v1'

class EvergreenMod(IlsMod):

    def __init__(self):
        self.host = '10.0.0.58'
        self.path = GATEWAY_PATH
        self.http = None
        pass

    def init(self):
        self.http = urllib3.HTTPSConnectionPool(self.host, 
            cert_reqs='CERT_NONE', assert_hostname=False)
        pass

    '''
    def gateway_url(self):

        if self.host.lower().startswith(('http://', 'https://')):
            return '%s/%s' % (self.host, self.path)

        return 'http://%s/%s' % (self.host, self.path)
        '''


    def gateway_request(self, service, method, *params):

        post_params = urlencode({'service': service, 'method': method})

        for p in params:
            post_params += '&param=%s' % quote(json.dumps(p), "'/")

        try:
            response = self.http.urlopen('POST', GATEWAY_PATH, body=post_params)
        except Exception as e:
            # log this?
            sys.stderr.write('%s => %s\n' % (repr(e), repr(params)))
            raise e

        return self.handle_gateway_response(response)

    def handle_gateway_response(self, response):

        data = response.data
        
        obj = json.loads(data)

        stat = int(obj['status'])

        if stat != 200:
            raise Exception(
                'Gateway Request Returns non-success status: %d' % stat)

        return obj['payload']

    def login(self, msg): 
        ''' Respond to login requests '''

        username = msg.get_field_value(fspec.login_uid.code)
        password = msg.get_field_value(fspec.login_pwd.code)

        resp = self.gateway_request(
            'open-ils.auth',
            'open-ils.auth.login',
            {'username': username, 'password': password, 'type': 'temp'}
        )

        # only expecting a single response
        auth_resp = resp[0]

        if auth_resp['textcode'] == 'SUCCESS':

            return Message(
                spec = mspec.login_resp,
                fixed_fields = [
                    FixedField(ffspec.ok, '1')
                ]
            )

        else:

            return Message(
                spec = mspec.login_resp,
                fixed_fields = [
                    FixedField(ffspec.ok, '0')
                ]
            )


