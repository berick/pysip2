#!/usr/bin/python3
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
PYTHONPATH=../src/ ./checkout.py <item_barcode> <patron_barcode>
'''

logging.config.fileConfig('pysip2-client.ini')
config = configparser.ConfigParser()
config.read('pysip2-client.ini')

copy_barcode = sys.argv[1]
patron_barcode = sys.argv[2]

server = config['client']['server']
port = config['client']['port']
institution = config['client']['institution']
username = config['client']['username']
password = config['client']['password']
location_code = config['client']['location_code']

client = pysip2.client.Client(server, int(port))
client.default_institution = institution
client.connect()
client.login(username, password, location_code)
resp = client.checkout_request(copy_barcode, patron_barcode)

if resp.get_fixed_field_by_name('ok').value == '1':
    print(" * Checkout Succeeded")
else:
    print(" * Checkout Failed")

print("Full Checkout Response:\n" + repr(resp))

client.disconnect()
