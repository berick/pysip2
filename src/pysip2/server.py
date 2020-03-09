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
import sys, socket, random, time, socket, threading
import logging, logging.config, getopt, configparser
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.spec import TEXT_ENCODING, LINE_TERMINATOR, SOCKET_BUFSIZE
from pysip2.message import Message, FixedField, Field
from pysip2.ils import IlsMod
from pysip2.ilsmods.evergreen import EvergreenMod

class SIPServer(object):

    def __init__(self, host, port, ils):
        self.host = host
        self.port = port
        self.ils  = ils
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
        ''' Starts a new SIPServerConnection '''

        con = SIPServerConnection(client, address, self.ils)

        try:
            con.listen_loop()
        except Exception as err:
            logging.warn(
                "SIPServerConnection from %s exited unexpectedly: %s" % (
                    address, err
                )
            )


class SIPServerConnection(object):
    ''' Models a single client connection to the SIPServer. '''

    LINE_TERMINATOR_LEN = len(LINE_TERMINATOR)

    def __init__(self, client, address, ils):
        self.client = client
        self.address = address
        self.ils = ils

    def child_init(self):
        ''' Called when the thread starts '''
        pass

    def child_complete(self):
        ''' Called when the child is done reading messages '''
        pass

    def disconnect(self):
        logging.debug('disconnecting client: ' + repr(self.address));

        try:
            self.client.close()
        except Exception as err:
            logging.warn(
                "Error closing client socket for %s : %s" % (
                    self.address, err
                )
            )

    def send_msg(self, msg):
        ''' Sends a Message to the client '''

        msg_txt = str(msg)
        logging.debug('OUTBOUND: %s' % msg_txt)
        self.client.send(bytes(msg_txt + LINE_TERMINATOR, TEXT_ENCODING))

    def listen_loop(self):
        ''' Handle client requests. '''

        self.child_init()

        while True:
            msg = self.read_one_message()
            if msg is None: break
            self.dispatch_message(msg)

        self.child_complete()

    def read_one_message(self):

        msg_txt = ''
        while True:

            buf = self.client.recv(SOCKET_BUFSIZE)

            if buf is None or len(buf) == 0: # client disconnected
                logging.info("Client connection severed.  Disconnecting");
                self.disconnect()
                return None

            msg_txt = msg_txt + buf.decode(TEXT_ENCODING)

            if msg_txt[-SIPServerConnection.LINE_TERMINATOR_LEN:] == LINE_TERMINATOR:
                break

        logging.debug("INBOUND: " + msg_txt)

        return Message(msg_txt = msg_txt)

    def dispatch_message(self, msg):
        msg_code = msg.spec.code

        resp = self.ils.handle_request(msg)

        if resp is not None:
            self.send_msg(resp)
        else:
            logging.warn("no handler defined for message type: " + msg_code)
            
if __name__ == '__main__':

    logging.config.fileConfig('pysip2-server.ini')
    config = configparser.ConfigParser()
    config.read('pysip2-server.ini')

    server = config['server']
    host = server.get('host', '')
    port = server.get('port', 6001)

    #ils = ILSMod()
    ils = EvergreenMod()
    ils.init()
    SIPServer(host, int(port), ils).listen()

