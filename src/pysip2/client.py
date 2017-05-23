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
import sys, socket, ssl, random, time, logging
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.spec import TEXT_ENCODING, LINE_TERMINATOR, SOCKET_BUFSIZE
from pysip2.message import Message, FixedField, Field

class ProtocolError(Exception):
    ''' Invalid messages fields, header values, etc '''
    pass

class Client(object):
    ''' SIP2 client connection '''

    LINE_TERMINATOR_LEN = len(LINE_TERMINATOR)

    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.sock = None
        self.default_institution = None # optional default institution
        self.terminal_pwd = None # optional terminal password
        self.client_log = ClientLog()

    def ssl_args(self, **kwargs):
        ''' Enable SSL connections and apply SSL options

        kwargs:
            enabled : turn on SSL for this connection
            require_valid_cert : fail on untrusted certificate
            check_hostname : fail if the certificate hostname does 
                not match SIP server hostname.
        '''
        self.ssl_enabled = kwargs.get('enabled', False)
        self.ssl_require_valid_cert = kwargs.get('require_valid_cert', True)
        self.ssl_check_hostname = kwargs.get('check_hostname', True)

    def connect(self):
        ''' Connects to the SIP2 server '''
        logging.debug(
            'connecting to server %s:%s' % (self.server, self.port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server, self.port))

        if self.ssl_enabled: self.setup_ssl();

    def setup_ssl(self):
        context = ssl.create_default_context()

        if self.ssl_require_valid_cert:
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = self.ssl_check_hostname
        else:
            logging.warn('SSL certificate checks disabled. ' +
                'This is probably not what you want!')
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        logging.debug('setting up SSL connection')

        self.sock = context.wrap_socket(
            self.sock, server_hostname=self.server)

    def disconnect(self):
        ''' Disconnects from the SIP2 server '''
        logging.debug(
            'disconnecting from server %s:%s' % (self.server, self.port))
        self.sock.close()

    def log_summary(self):
        ''' Log message summary statistics '''
        self.client_log.log_summary()

    def log_messages(self):
        ''' Log all messages and summary statistics '''
        self.client_log.log_messages()

    def send_msg(self, msg):
        ''' Sends a Message to the server '''
        msg_txt = str(msg)
        logging.debug('SENDING: %s' % msg_txt)
        self.client_log.start_msg(msg.spec)
        self.sock.send(bytes(msg_txt + LINE_TERMINATOR, TEXT_ENCODING))

    def recv_msg(self):
        ''' Receives a Message from the server '''

        msg_txt = ''
        while True:

            buf = self.sock.recv(SOCKET_BUFSIZE)

            if buf is None or len(buf) == 0: # server kicked us off
                try:
                    # disconnect if we can
                    self.disconnect()
                except:
                    pass
                raise IOError("Disconnected from SIP2 server");

            msg_txt = msg_txt + buf.decode(TEXT_ENCODING)

            if msg_txt[-Client.LINE_TERMINATOR_LEN:] == LINE_TERMINATOR:
                break

        self.client_log.finish_msg()
        logging.debug("RECEIVED: " + msg_txt)

        return Message(msg_txt = msg_txt)


    def sc_status(self, **kwargs):
        ''' Send a "SC Status" request to the server.

        kwargs
            - status_code
            - max_print_width
            - protocol_version
        '''
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


    def login(self, username, password, location):
        ''' Login to SIP2 server.

        Returns True on success, False on login failure,
        Raises socket exception on communcation failures.
        '''

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


    def item_info_request(self, item_id, **kwargs):
        ''' Sends an Item Information Request message

        kwargs
            - institution 
                -- required if default_institution is unset
        '''

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

    def patron_status_request(self, patron_id, **kwargs):
        ''' Sends a Patron Status Request message.

        optional kwargs
            - institution 
                -- required if default_institution is unset
            - patron_pwd
        '''

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

    def patron_info_request(self, patron_id, **kwargs):
        ''' Send a Patron Information Request message.

        optional kwargs
            - institution 
                -- required if default_institution is unset
            - summary
                -- determines what detailed information to request, if any
            - patron_pwd
            - start_item
            - end_item
        '''

        logging.debug("patron_information_request() for %s" % patron_id)

        # summary may contain up to 1 "Y" value.
        summary = kwargs.get('summary', '          ')
        if summary.count('Y') > 1:
            raise ProtocolError(
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

    def checkout_request(self, item_id, patron_id, **kwargs):
        ''' Send a Checkout message.

        kwargs
            - institution
                -- required if default_institution is unset
            - sc_renewal_policy
            - no_block
            - nb_due_date
            - item_properties
            - fee acknowledged
            - cancel
        '''

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

    def checkin_request(self, item_id, current_location, **kwargs):
        ''' Send a Checkin message.

        kwargs
            - institution
                -- required if default_institution is unset
            - no_block
            - return_date
            - item_properties
            - cancel
        '''

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


class ClientLog(object):
    '''
    Collect round-trip timing information for client requests.
    '''

    class ClientMessage(object):
        '''
        Models a single round-trip message
        '''
        def __init__(self, spec, start_time):
            self.spec = spec
            self.start_time = start_time
            self.end_time = 0
            self.duration = 0

        def __str__(self):
            return _('duration: {0:.3f} [{1}] {2}').format(
                self.duration, self.spec.code, self.spec.label)

    def __init__(self):
        self.messages = []
        self.current_msg = None

    def start_msg(self, spec):
        ''' Start tracking a new message '''
        self.current_msg = ClientLog.ClientMessage(spec, time.time())

    def finish_msg(self):
        ''' Complete collecting data on the current message '''
        self.current_msg.end_time = time.time()
        self.current_msg.duration = \
            self.current_msg.end_time - self.current_msg.start_time
        self.messages.append(self.current_msg)
        self.current_msg = None

    def log_summary(self):
        ''' Logs summary information on collected messages '''

        if len(self.messages) == 0:
            logging.info(_('No messages collected'))
            return

        total_duration = 0
        for msg in self.messages:
            total_duration = total_duration + msg.duration

        avg_duration = total_duration / len(self.messages)
        logging.info(_('Total request time {0:.3f}').format(total_duration))
        logging.info(_('Average request time {0:.3f}').format(avg_duration))

    def log_messages(self):
        ''' Logs data on all collected messages '''

        if len(self.messages) == 0:
            logging.info(_('No messages collected'))
            return

        for msg in self.messages:
            logging.info(str(msg))
