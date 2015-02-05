#!/usr/bin/python3
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
client.connect()
client.login(username, password, location_code)
resp = client.sc_status()

print("All Fields:\n" + repr(resp))

print("offline OK value => " + \
    resp.get_fixed_field_by_name('offline_ok').value + "\n")

client.disconnect()

