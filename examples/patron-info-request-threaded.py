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
import sys, logging, logging.config, getopt, configparser, threading, time
import pysip2.client

logging.config.fileConfig('pysip2-client.ini')
config = configparser.ConfigParser()
config.read('pysip2-client.ini')

server = config['client']['server']
port = config['client']['port']
institution = config['client']['institution']
username = config['client']['username']
password = config['client']['password']
location_code = config['client']['location_code']

class ThreadedClient(threading.Thread):

    def __init__(self, barcode):
        super(ThreadedClient, self).__init__()
        self.barcode = barcode

    def run(self):
        client = pysip2.client.Client(server, int(port))
        client.default_institution = institution
        client.connect()
        client.login(username, password, location_code)

        for i in range(10):
            resp = client.patron_info_request(self.barcode)
            time.sleep(.02)

        client.disconnect()
        client.log_messages()


thread1 = ThreadedClient(sys.argv[1])
thread2 = ThreadedClient(sys.argv[2])
thread1.start()
time.sleep(1) # give first login a chance to complete
thread2.start()

