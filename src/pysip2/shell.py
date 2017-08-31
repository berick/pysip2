# -----------------------------------------------------------------------
# Copyright (C) 2017 King County Library System
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
#
# Console code heavily inspired by
# https://gist.github.com/rduplain/899f6a5e583a85668822
# -----------------------------------------------------------------------
import sys, logging, code, readline, shlex, time
from gettext import gettext as _
import logging.config, getopt, configparser
import pysip2.client

# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------
PS1 = _('sipsh% ')
PS2 = _('...')


# -----------------------------------------------------------------
# TODO: 
# - optional parameters
# -----------------------------------------------------------------

def usage(exit_code=0):
    print(_('''

    -h, --help
        Display this help message

    -c <file>, --config <file> 
        Override the default configuration file.  The default file is 
        'pysip2-client.ini' in the current working directory.

    -a, --autostart
        Automatically connect, login, and send a status request to the 
        SIP server using the configuration options in the configuration 
        .ini file.  Without specifying this option, the user must 
        manually execute the 'start' command or a combination of
        'connect', 'login', and 'status'.
    '''))
    sys.exit(exit_code)

class Console(object):
    ''' Reads a line of input from stdin and passes it off to 
        CommandRunner for execution. 
    '''

    def __init__(self, runner):
        self.runner = runner

    def interact(self, locals=None):
        class MyConsole(code.InteractiveConsole):
            def runsource(code_console, line, filename=None, symbol=None):
                self.runner.run(line)
                return False

        sys.ps1 = PS1
        sys.ps2 = PS2
        MyConsole(locals=locals, filename="<sipsh>").interact(banner='')

class CommandRunner(object):
    ''' Executes a single command '''

    def __init__(self, config):
        self.client = None
        self.config = config
        self.commands = {}

        # sorted list of command names lets us display them in
        # add-order in the help display
        self.commands_sorted = []

        self.add_command('help', self.help, _('Display help message'))
        self.add_command('echo', self.echo, _('Echo command with arguments'))
        self.add_command('exit', self.exit, _('Exit shell'))

        self.add_command('connect', self.connect, 
            _('Open a network connection to the SIP server.'))

        self.add_command('disconnect', self.disconnect, 
            _('Close a network connection to the SIP server.'))

        self.add_command('login', self.login, _('Send a 93 Login request.'))

        self.add_command('status', self.status, 
            _('Send a SC Status (99) request message.'))

        self.add_command('start', self.start,
            _('Executes "connect" + "login" + "status" commands.'))

        self.add_command('patron-status', self.patron_status,
            _('Send a Patron Status Request (23) message.'), 
            [{'required' : True, 'label' : _('patron-barcode')}]
        )

        self.add_command('patron-info', self.patron_info,
            _('Send a Patron Information Request (63) message.'), 
            [{'required' : True, 'label' : _('patron-barcode')}]
        )

        self.add_command('checkout', self.checkout,
            _('Send a Checkout Request (11) message.'), 
            [
                {'required' : True, 'label' : _('item-barcode')},
                {'required' : True, 'label' : _('patron-barcode')}
            ]
        )

        self.add_command('checkin', self.checkin,
            _('Send a Checkin Request (09) message.'), 
            [{'required' : True, 'label' : _('item-barcode')}]
        )

        self.add_command('server', self.set_sip_attr,
            _('View or set the current SIP server.'),
            [{'required' : False, 'label' : _('hostname')}]
        )

        self.add_command('port', self.set_sip_attr,
            _('View or set the current SIP port.'),
            [{'required' : False, 'label' : _('port')}]
        )

        self.add_command('username', self.set_sip_attr,
            _('View or set the current SIP username.'),
            [{'required' : False, 'label' : _('username')}]
        )

        self.add_command('password', self.set_sip_attr,
            _('View or set the current SIP password.'),
            [{'required' : False, 'label' : _('password')}]
        )

        self.add_command('institution', self.set_sip_attr,
            _('View or set the current SIP institution.'),
            [{'required' : False, 'label' : _('institution')}]
        )

        self.add_command('location_code', self.set_sip_attr,
            _('View or set the current SIP location code.'),
            [{'required' : False, 'label' : _('location-code')}]
        )

        self.add_command('timing', self.set_conf_attr,
            _('View or set the message timing reporting'),
            [{'required' : False, 'label' : _('on/off')}]
        )

    def add_command(self, cmd, fn, desc, args=[]):
        self.commands_sorted.append(cmd)
        self.commands[cmd] = {
            'fn' : fn,
            'desc': desc,
            'args' : args,
            'min_args' : len([a for a in args if a['required']])
        }

    def help(self, cmd, *args):
        print(_('Commands:'))
        for cmd in self.commands_sorted:
            blob = self.commands[cmd]
            print(_('  {0} {1}\n    - {2}').format(
                cmd, 
                ' '.join([_('<{0}>').format(a['label']) for a in blob['args']]),
                blob['desc']
            ))
        return True
        
    def exit(self, cmd, *args):
        print(_('Goodbye'))
        sys.exit(0)

    def echo(self, cmd, *args):
        print(_('echo args={0}').format(str(list(args))))

    def connect(self, cmd, *args):
        conf = self.config
        self.disconnect(cmd, args)

        self.client = pysip2.client.Client(conf.server, int(conf.port))
        self.client.default_institution = conf.institution
        #client.ssl_args(...) 
        try:
            self.client.connect()
        except:
            print(_('Unable to connect to server {0} port {1}').format(
                conf.server, conf.port))
            self.client = None
            return False

        print (_('Connect OK'))
        return True

    def disconnect(self, cmd, *args):

        if self.client is None:
            return
        
        self.client.disconnect()
        print(_('Disconnected from {0}').format(self.config.server))
           

    def login(self, cmd, *args):
        conf = self.config
        if self.client.login(conf.username, conf.password, conf.location_code):
            print(_('Login OK'))
            return True

        print(_('Login Failed'))
        return False

    def status(self, cmd, *args):
        resp = self.client.sc_status()
        if resp.get_fixed_field_by_name('online_status').value == 'Y':
            print(_('Server is online'))
            return True

        print(_('Server is NOT online'))
        print(repr(resp))
        return False

    def start(self, cmd, *args):
        if self.connect(cmd, *args):
            if self.login(cmd, *args):
                self.status(cmd, *args)

    def patron_status(self, cmd, *args):
        resp = self.client.patron_status_request(args[0])
        print(repr(resp))
        return True

    def patron_info(self, cmd, *args):
        resp = self.client.patron_info_request(args[0])
        print(repr(resp))
        return True

    def checkout(self, cmd, *args):
        resp = self.client.checkout_request(args[0], args[1])
        print(repr(resp))
        return True

    def checkin(self, cmd, *args):
        resp = self.client.checkin_request(args[0], self.config.location_code)
        print(repr(resp))
        return True

    def set_sip_attr(self, attr, *args):

        if len(args) == 0:
            print(getattr(self.config, attr))
            return

        # Any changes to SIP connection attributes require a reconnect.
        # Force a disconnect, let the user reconnect.
        if self.client is not None:
            print(_('Disconnecting from {0}...').format(self.config.server))
            self.client.disconnect()
            self.client = None

        setattr(self.config, attr, args[0])
        print(_('Set SIP attribute "{0}" to "{1}"').format(attr, args[0]))

        return True

    def set_conf_attr(self, attr, *args):
        ''' Just like set_sip_attr minus the disconnect '''

        if len(args) == 0:
            print(getattr(self.config, attr))
            return

        setattr(self.config, attr, args[0])
        print(_('Set config option "{0}" to "{1}"').format(attr, args[0]))

        return True


    def run(self, line):
        tokens = shlex.split(line, comments=True)
        command, args = tokens[0], tokens[1:]

        if command not in self.commands:
            print(_('Command not found: {0}').format(command), file=sys.stderr)
            return

        # These commands require an active SIP connection
        if command in ['status','patron-status','patron-info',
            'item-info','checkout','checkin'] and not self.client:
            print(_('Command cannot be executed without a SIP server '
                'connection.  Try running the "start" command.'))
            return
           
        cmd = self.commands[command]

        if len(args) < cmd['min_args']:
            print(_('Command {0} requires at least {1} argument(s)').format(
                command, cmd['min_args']), file=sys.stderr)
            return

        start_time = time.time()
        res = cmd['fn'](command, *args)
        end_time = time.time()

        if self.config.timing == 'on':
            print(_('Request time: %0.2f seconds' % (end_time - start_time)))

        return res

class ConfigHandler(object):
    def __init__(self):
        self.configfile = 'pysip2-client.ini'
        self.server = None
        self.port = None
        self.institution = None
        self.username = None
        self.password = None
        self.autostart = False
        self.timing = 'off'

    def setup(self):

        logging.config.fileConfig(self.configfile)
        config = configparser.ConfigParser()
        config.read(self.configfile)

        # prevent stdout debug logs from cluttering the shell.
        # TODO: make it possible to change this from within the shell.
        logging.getLogger().setLevel('WARNING')

        if 'client' not in config: return

        self.server = config['client'].get('server', None)
        self.port = config['client'].get('port', None)
        self.institution = config['client'].get('institution', None)
        self.username = config['client'].get('username', None)
        self.password = config['client'].get('password', None)
        self.location_code = config['client'].get('location_code', None)

    def read_ops(self):

        try:
            opts, args = getopt.getopt(
                sys.argv[1:], 
                "hac:", 
                ["help", "autostart", "config="]
            )
        except getopt.GetoptError as err:
            print(str(err), file=sys.stderr)
            usage(2)
        for o, a in opts:
            if o in ('-h', '--help'):
                usage()
                pass
            elif o in ('-a', '--autostart'):
                self.autostart = True
            elif o in ('-c', '--config'):
                self.configfile = a
            else:
                print('Uhandled option', file=sys.stderr)

if __name__ == '__main__':
    config = ConfigHandler()
    runner = CommandRunner(config)
    console = Console(runner)
    config.read_ops()
    config.setup()

    if config.autostart:
        runner.start()

    console.interact()


