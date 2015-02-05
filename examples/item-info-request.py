#!/usr/bin/python3
import sys, logging, logging.config, getopt, configparser
import pysip2.client

'''
PYTHONPATH=../src/ ./item-info-request.py <copy_barcode>
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

copy_barcode = sys.argv[1]

client = pysip2.client.Client(server, int(port))
client.default_institution = institution
client.connect()
client.login(username, password, location_code)
resp = client.item_info_request(copy_barcode)

print("All Fields:\n" + repr(resp))

# example of accessing a field by code
print("title: %s\n" % resp.get_field_by_code('AJ').value)

client.disconnect()

