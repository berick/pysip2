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

import sys, socket, random, time, logging
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.spec import TEXT_ENCODING, LINE_TERMINATOR, SOCKET_BUFSIZE
from pysip2.message import Message, FixedField, Field


# used for SIP2-level errors
class ClientError(Exception):
    pass

class Client(object):
    LINE_TERMINATOR_LEN = len(LINE_TERMINATOR)

    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.sock = None
        self.default_institution = None # optional default institution
        self.terminal_pwd = None # optional terminal password

    # may raise socket.error
    def connect(self):
        logging.debug(
            'connecting to server %s:%s' % (self.server, self.port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server, self.port))

    def disconnect(self):
        logging.debug(
            'disconnecting from server %s:%s' % (self.server, self.port))
        self.sock.close()

    def send_msg(self, msg):
        msg_txt = str(msg)
        logging.debug('sending message: %s' % msg_txt)
        self.sock.send(bytes(msg_txt + LINE_TERMINATOR, TEXT_ENCODING))

    def recv_msg(self):
        msg_txt = ''

        while True:

            buf = self.sock.recv(SOCKET_BUFSIZE)

            if buf is None or buf == '': # server kicked us off
                try:
                    # disconnect if we can
                    self.disconnect()
                except:
                    pass
                raise IOError("Disconnected from SIP2 server");

            msg_txt = msg_txt + buf.decode(TEXT_ENCODING)

            if msg_txt[-Client.LINE_TERMINATOR_LEN:] == LINE_TERMINATOR:
                break

        logging.debug("received message: " + msg_txt)

        return Message(msg_txt = msg_txt)


    '''
    kwargs
        - status_code
        - max_print_width
        - protocol_version
    '''
    def sc_status(self, **kwargs):

        logging.debug("sending sc status")

        msg = Message(
            spec = mspec.sc_status,
            fixed_fields = [
                FixedField(
                    ffspec.status_code,
                    kwargs.get('status_code', '0')),
                FixedField(
                    ffspec.max_print_width,
                    kwargs.get('max_print_width', '100')),
                FixedField( 
                    ffspec.protocol_version, 
                    kwargs.get('protocol_version', '2.00'))
            ]
        )

        self.send_msg(msg)
        return self.recv_msg()


    '''
    Login to SIP2 server

    Returns True on success, False on login failure,
    raises socket exception on communcation failures.
    '''
    def login(self, username, password, location):

        logging.debug(
            "logging in with username %s @ location %s" % (
            username, location))

        msg = Message(
            spec = mspec.login,
            fixed_fields = [
                FixedField(ffspec.uid_algo, '0'),
                FixedField(ffspec.pwd_algo, '0')
            ],
            fields = [
                Field(fspec.login_uid, username),
                Field(fspec.login_pwd, password),
                Field(fspec.location_code, location)
            ]
        )

        self.send_msg(msg)
        resp = self.recv_msg()

        # the OK field is 1/0 value in the fixed fields
        if resp.fixed_fields[0].value == '1':
            logging.debug("login succeeded for %s" % username)
            return True

        logging.info("login failed for %s : %s" % (username, resp))
        return False


    '''
    kwargs 
        - institution
    '''
    def item_info_request(self, item_id, **kwargs):

        logging.debug("item_info_request() for %s" % item_id)

        msg = Message(
            spec = mspec.item_info, 
            fixed_fields = [
                FixedField(ffspec.date, Message.sipdate())
            ]
        )

        msg.add_field(fspec.institution_id, 
            kwargs.get('institution', self.default_institution))

        msg.add_field(fspec.item_id, item_id)
        msg.maybe_add_field(fspec.terminal_pwd, self.terminal_pwd)
        
        self.send_msg(msg)
        return self.recv_msg()

    '''
    kwargs
        - institution
        - patron_pwd
    '''
    def patron_status_request(self, patron_id, **kwargs):

        logging.debug("patron_status_request() for %s" % patron_id)

        msg = Message(
            spec = mspec.patron_status,
            fixed_fields = [
                FixedField(ffspec.language, '000'),
                FixedField(ffspec.date, Message.sipdate())
            ]
        )

        msg.add_field(fspec.institution_id, 
            kwargs.get('institution', self.default_institution))

        msg.add_field(fspec.patron_id, patron_id)
        msg.maybe_add_field(fspec.terminal_pwd, self.terminal_pwd)
        msg.maybe_add_field(fspec.patron_pwd, kwargs.get('patron_pwd'))

        self.send_msg(msg)
        return self.recv_msg()

    '''
    kwargs
        - institution
        - summary
        - patron_pwd
        - start_item
        - end_item
    '''
    def patron_info_request(self, patron_id, **kwargs):

        logging.debug("patron_information_request() for %s" % patron_id)

        # summary may contain up to 1 "Y" value.
        summary = kwargs.get('summary', '          ')
        if summary.count('Y') > 1:
            raise ClientError(
                'Too many summary values requested in patron info request')

        msg = Message(
            spec = mspec.patron_info,
            fixed_fields = [
                FixedField(ffspec.language, '000'),
                FixedField(ffspec.date, Message.sipdate()),
                FixedField(ffspec.summary, summary)
            ],
        )

        msg.add_field(fspec.institution_id, 
            kwargs.get('institution', self.default_institution))

        msg.add_field(fspec.patron_id, patron_id),
        msg.maybe_add_field(fspec.terminal_pwd, self.terminal_pwd)
        msg.maybe_add_field(fspec.patron_pwd, kwargs.get('patron_pwd'))
        msg.maybe_add_field(fspec.start_item, kwargs.get('start_item'))
        msg.maybe_add_field(fspec.end_item, kwargs.get('end_item'))

        self.send_msg(msg)
        return self.recv_msg()

    '''
    kwargs
        - institution
        - sc_renewal_policy
        - no_block
        - nb_due_date
        - item_properties
        - fee acknowledged
        - cancel
    '''
    def checkout_request(self, item_id, patron_id, **kwargs):

        logging.debug(
            "checkout_request() for patron=%s and item=%s" % (
            patron_id, item_id))

        msg = Message(
            spec = mspec.checkout,
            fixed_fields = [
                FixedField(
                    ffspec.sc_renewal_policy,
                    kwargs.get('sc_renewal_policy', 'N')),
                FixedField(
                    ffspec.no_block,
                    kwargs.get('no_block', 'N')),
                FixedField(ffspec.date, Message.sipdate()),
                FixedField(
                    ffspec.nb_due_date, 
                    kwargs.get('nb_due_date', Message.sipdate()))
            ],
        )

        msg.add_field(
            fspec.institution_id, 
            kwargs.get('institution', self.default_institution))

        msg.add_field(fspec.patron_id, patron_id),
        msg.add_field(fspec.item_id, item_id),

        msg.maybe_add_field(fspec.terminal_pwd, self.terminal_pwd)
        msg.maybe_add_field(
            fspec.item_properties, kwargs.get('item_properties'))

        msg.maybe_add_field(fspec.patron_pwd, kwargs.get('patron_pwd'))
        msg.maybe_add_field(
            fspec.fee_acknowledged, kwargs.get('fee_acknowledged'))
        msg.maybe_add_field(fspec.cancel, kwargs.get('cancel'))

        self.send_msg(msg)
        return self.recv_msg()

    '''
    kwargs
        - institution
        - no_block
        - return_date
        - item_properties
        - cancel
    '''
    def checkin_request(self, item_id, current_location, **kwargs):

        logging.debug(
            "checkin_request() for item %s" % (item_id))

        msg = Message(
            spec = mspec.checkin,
            fixed_fields = [
                FixedField(
                    ffspec.no_block,
                    kwargs.get('no_block', 'N')),
                FixedField(ffspec.date, Message.sipdate()),
                FixedField(
                    ffspec.return_date, 
                    kwargs.get('return_date', Message.sipdate()))
            ],
        )

        msg.add_field(
            fspec.institution_id, 
            kwargs.get('institution', self.default_institution))

        msg.add_field(fspec.current_location, current_location),
        msg.add_field(fspec.item_id, item_id),

        msg.maybe_add_field(fspec.terminal_pwd, self.terminal_pwd)
        msg.maybe_add_field(
            fspec.item_properties, kwargs.get('item_properties'))
        msg.maybe_add_field(fspec.cancel, kwargs.get('cancel'))

        self.send_msg(msg)
        return self.recv_msg()

