#!/usr/bin/python3
import sys, logging, logging.config, getopt, configparser
import pysip2.client

'''
PYTHONPATH=../src/ ./checkout-checkin.py <item_barcode> <patron_barcode>
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

resp = client.checkin_request(copy_barcode, location_code)

if resp.get_fixed_field_by_name('ok').value == '1':
    print(" * Checkin Succeeded")
else:
    print(" * Checkin Failed")

print("Full Checkin Response:\n" + repr(resp))

client.disconnect()

