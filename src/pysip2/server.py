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

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):
        ''' Wait for new clients to connect '''
        self.sock.listen(5)

        while True:

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

    server = config['server']
    host = server.get('host', '')
    port = server.get('port', 6001)

    Server(host, int(port)).listen()

