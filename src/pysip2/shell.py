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
import logging
import code
import readline
import sys
import shlex
from gettext import gettext as _
import logging.config, getopt, configparser
import pysip2.client

# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------
PS1 = _('sipsh% ')
PS2 = _('...')

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
        self.add_command('echo', self.echo)
        self.add_command('exit', self.exit)
        self.add_command('quit', self.exit)
        self.add_command('connect', self.connect)
        self.add_command('login', self.login)
        self.add_command('status', self.status)
        self.add_command('start', self.start)
        self.add_command('patron-info', self.patron_info)

    def add_command(self, cmd, fn):
        self.commands[cmd] = fn

    def exit(self, *args):
        print(_('Goodbye'))
        sys.exit(0)

    def echo(self, *args):
        print(_('echo args={0}').format(str(list(args))))

    def connect(self, *args):
        conf = self.config
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

    def login(self, *args):
        conf = self.config
        if self.client.login(conf.username, conf.password, conf.location_code):
            print(_('Login OK'))
            return True

        print(_('Login Failed'))
        return False

    def status(self, *args):
        resp = self.client.sc_status()
        if resp.get_fixed_field_by_name('online_status').value == 'Y':
            print(_('Server is online'))
            return True

        print(_('Server is NOT online'))
        print(repr(resp))
        return False

    def start(self, *args):
        if self.connect(*args):
            if self.login(*args):
                self.status(*args)

    def patron_info(self, *args):
        if len(args) == 0:
            print(_('Patron barcode required'))
            return False

        resp = self.client.patron_info_request(args[0])
        print(repr(resp))
        return True

    def run(self, line):
        tokens = shlex.split(line, comments=True)
        command, args = tokens[0], tokens[1:]

        if command not in self.commands:
            print(_('Command not found: {0}').format(command), file=sys.stderr)
            return

        return self.commands[command](*args)

class ConfigHandler(object):
    def __init__(self):
        self.server = None
        self.port = None
        self.institution = None
        self.username = None
        self.password = None

    def setup(self, configfile):

        logging.config.fileConfig(configfile)
        config = configparser.ConfigParser()
        config.read(configfile)

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

if __name__ == '__main__':
    config = ConfigHandler()
    runner = CommandRunner(config)
    console = Console(runner)
    config.setup('pysip2-client.ini')
    console.interact()


