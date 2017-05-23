#!/usr/bin/env python3
# -----------------------------------------------------------------------
# Copyright (C) 2015 King County Library System
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
import sys, logging, logging.config, getopt, configparser
import pysip2.client

'''
PYTHONPATH=../src/ ./sc-status.py
'''

logging.config.fileConfig('pysip2-client.ini')
config = configparser.ConfigParser()
config.read('pysip2-client.ini')

server = config['client']['server']
port = config['client']['port']
institution = config['client']['institution']
username = config['client']['username']
password = config['client']['password']
location_code = config['client']['location_code']

client = pysip2.client.Client(server, int(port))
client.default_institution = institution

client.ssl_args(
    enabled = config.getboolean('ssl', 'enabled'),
    require_valid_cert = config.getboolean('ssl', 'require_valid_cert'),
    check_hostname = config.getboolean('ssl', 'check_hostname')
)

client.connect()
client.login(username, password, location_code)
resp = client.sc_status()

logging.info('\n'+repr(resp))

logging.info("offline OK value => " + \
    resp.get_fixed_field_by_name('offline_ok').value)

# example access fixed fields by position
ff = resp.fixed_fields[0]
logging.info('First fixed field: %s => %s' % (ff.spec.label, ff.value))

client.disconnect()
client.log_messages()
client.log_summary()

