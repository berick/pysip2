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
import sys, socket, urllib3, uuid
import logging, logging.config, getopt, configparser
from urllib.parse import urlencode
from gettext import gettext as _
from pysip2.spec import TEXT_ENCODING, LINE_TERMINATOR, SOCKET_BUFSIZE
from pysip2.message import Message, FixedField, Field

class ServerThread(object):
    ''' Models a single client connection to the SIPServer. '''

    LINE_TERMINATOR_LEN = len(LINE_TERMINATOR)

    ''' Connection instances use a shared HTTP(S) connection pool '''
    http_pool = None

    def __init__(self, sip_client, sip_address):
        self.sip_client = sip_client
        self.sip_address = sip_address
        self.http_host = None
        self.http_port = None
        self.http_path = None

    def thread_init(self):
        ''' Called when the thread starts '''

        # TODO configs
        self.http_host = '10.0.0.58'
        self.http_port = 443
        self.http_path = '/sip2-mediator'
        self.session_key = uuid.uuid4().hex

        if not ServerThread.http_pool:

            # TODO configs
            ServerThread.http_pool = urllib3.HTTPSConnectionPool(
                self.http_host, 
                port=self.http_port,
                cert_reqs='CERT_NONE', 
                assert_hostname=False
            )

    def thread_complete(self):
        ''' Called when the child is done reading messages '''
        pass

    def disconnect(self):
        logging.debug('disconnecting client: ' + repr(self.sip_address));

        try:
            self.sip_client.close()
        except Exception as err:
            logging.warn(
                "Error closing client socket for %s : %s" % (
                    self.sip_address, err
                )
            )

    def send_sip_msg(self, msg):
        ''' Sends a Message to the client '''

        msg_txt = str(msg)
        logging.debug('OUTBOUND: %s' % msg_txt)
        self.sip_client.send(bytes(msg_txt + LINE_TERMINATOR, TEXT_ENCODING))

    def listen_loop(self):
        ''' Handle client requests. '''

        self.thread_init()

        while True:
            msg = self.read_one_message()
            if msg is None: break
            self.dispatch_message(msg)

        self.thread_complete()

    def read_one_message(self) -> Message:

        msg_txt = ''
        while True:

            # TODO timeout / poll to check for global shutdown flag
            buf = self.sip_client.recv(SOCKET_BUFSIZE)

            if buf is None or len(buf) == 0: # client disconnected
                logging.info("Client connection severed.  Disconnecting");
                self.disconnect()
                return None

            msg_txt = msg_txt + buf.decode(TEXT_ENCODING)

            if msg_txt[-ServerThread.LINE_TERMINATOR_LEN:] == LINE_TERMINATOR:
                break

        logging.debug("INBOUND: " + msg_txt)

        return Message(msg_txt = msg_txt)

    def dispatch_message(self, msg):
        msg_code = msg.spec.code

        resp = self.http_request(msg)
        resp_msg = Message.from_json(resp)

        if resp_msg is None:
            logging.warn("No response received for message code: " + msg_code)
            self.disconnect()
        else:
            self.send_sip_msg(resp_msg)

    def http_request(self, msg) -> str:
        ''' Returns the response message as a JSON string '''

        post_params = urlencode(
            {'session': self.session_key, 'message': msg.to_json()}) 

        try:
            response = ServerThread.http_pool.urlopen(
                'POST', self.http_path, body=post_params)

        except Exception as e:
            logging.error('HTTP request failed %s' % repr(e))
            return None

        logging.debug("ILS Mediator returned: %s" % response.data)

        if response.status == 200:
            return response.data
        else:
            logging.warn(
                "ILS Mediator returned non-success status: %d" % response.status)
            return None

