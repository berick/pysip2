# -----------------------------------------------------------------------
# Copyright (C) 2020 King County Library System
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
import sys, socket, random, time, threading
import logging, logging.config, getopt, configparser
from gettext import gettext as _
from pysip2.server_thread import ServerThread

class Server(object):

    def __init__(self, config):

        self.sip_address = config.get('sip_address', '')
        self.sip_port = int(config.get('sip_port', 6001))

        self.http_address = config.get('http_address')
        self.http_port = int(config.get('http_port', 443))

        self.max_clients = int(config.get('max_clients', 150))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.sip_address, self.sip_port))

    def listen(self):
        ''' Wait for new clients to connect '''

        ServerThread.create_http_pool(
            self.max_clients, self.http_address, self.http_port)

        self.sock.listen(5)

        while True:

            # Poll for free thread space if we exceed the max.  Could
            # use a queue to track availability and block as needed, but
            # this works fine and means less complexity.
            log_max_threads = True # only log first
            while threading.active_count() >= self.max_clients:
                if log_max_threads:
                    logging.warn('Max thread count [%d] exceeded, waiting...' % 
                        self.max_clients)
                    log_max_threads = False
                time.sleep(5)

            try:
                client, address = self.sock.accept()
            except KeyboardInterrupt:
                logging.info("Exiting server on keyboard interrupt")
                return

            logging.debug("received connection from %s", address)

            # start a client handling thread
            threading.Thread(
                target = self.handle_client,
                args = (client, address)
            ).start()

    def handle_client(self, client, address):
        ''' Starts a new ServerThread '''

        con = ServerThread(client, address)

        try:
            con.listen_loop()
        except Exception as err:
            logging.warn(
                "ServerThread from %s exited unexpectedly: %s" % (
                    address, err
                )
            )
            
if __name__ == '__main__':

    logging.config.fileConfig('pysip2-server.ini')
    config = configparser.ConfigParser()
    config.read('pysip2-server.ini')

    Server(config['server']).listen()

