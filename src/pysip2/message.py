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
import time, logging, json
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.spec import STRING_COLUMN_PAD, SIP_DATETIME, LINE_TERMINATOR

class Field(object):
    '''Models a single SIP2 message field'''

    def __init__(self, spec, value=''):
        self.spec = spec
        self.value = value
    
    def __str__(self):
        return self.spec.code + (self.value or '') + '|'

    def __repr__(self):
        spaces = STRING_COLUMN_PAD - len(self.spec.label) - 5
        return '[%s] %s' % (self.spec.code, self.spec.label) \
            + ' '*spaces + ': ' + self.value

class FixedField(Field):
    '''Models a single SIP2 message fixed field'''
    def __str__(self):
        return self.value

    def __repr__(self):
        spaces = STRING_COLUMN_PAD - len(self.spec.label)
        return self.spec.label + ' '*spaces + ': ' + (self.value or '')

class Message(object):
    '''Models a complete SIP2 message.'''

    def __init__(self, **kwargs):
        self.fields = []
        self.fixed_fields = []
        self.msg_txt = ''

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.msg_txt != '':
            self.parse_txt()

    def to_json(self):

        msg_struct = {
            'code': self.spec.code,    
            'fixed_fields': [],
            'fields': []
        }

        for ff in self.fixed_fields:
            msg_struct['fixed_fields'].append(ff.value or '')

        for f in self.fields:
            msg_struct['fields'].append({f.spec.code: f.value})

        return json.dumps(msg_struct)

    @staticmethod
    def from_json(msg_json) -> 'Message':

        if msg_json == '' or msg_json is None:
            return None

        try:
            msg_struct = json.loads(msg_json)
        except Exception as e:
            logging.error("Error creating SIP message from JSON " + repr(e))
            return None

        # Start with a SIP message string which contains only the 
        # message code and its fixed fields.
        msg_txt = '%s%s%s' % (
            msg_struct['code'],
            ''.join(msg_struct['fixed_fields']),
            LINE_TERMINATOR
        )

        msg = Message(msg_txt=msg_txt)

        # Then add the Fields
        if 'fields' in msg_struct:
            for field in msg_struct['fields']:
                field_code = field.keys()[0]
                field_value = field[field_code]
                spec = FieldSpec.find_by_code(field_code)
                msg.add_field(spec, field_value)

        return msg
        
    def __str__(self):
        '''Returns a human-readable formatted SIP2 message.'''

        if self.msg_txt != '':
            return self.msg_txt

        new_txt = self.spec.code

        for ff in self.fixed_fields:
            new_txt = new_txt + str(ff)

        for field in self.fields:
            new_txt = new_txt + str(field)

        self.msg_txt = new_txt

        return self.msg_txt

    def __repr__(self):

        # note: this is a less than perfect i18n solution, but
        # creating fixed width i18n-friendly key/value pairs is hard.
        label_str = _("Label")
        code_str = _("Code")
        label_len = len(label_str)
        code_len = len(code_str)

        text = _("{0}{1}: {2}\n{3}{4}: {5}\n").format(
            label_str,
            ' '*(STRING_COLUMN_PAD - label_len),
            self.spec.label, 
            code_str,
            ' '*(STRING_COLUMN_PAD - code_len),
            self.spec.code
        )
            
        first = True
        for field in self.fixed_fields:
            if first:
                first = False
            else:
                text = text + '\n'
            text = text + repr(field)

        # only skip the opening newline if there were no fixed fields
        # to display
        first = len(self.fixed_fields) == 0
        for field in self.fields:
            if first:
                first = False
            else:
                text = text + '\n'
            text = text + repr(field)

        return text

    def add_field(self, spec, value):
        self.fields.append(Field(spec, value))

    def maybe_add_field(self, spec, value):
        if value is not None:
            self.fields.append(Field(spec, value))

    def get_field(self, code):
        '''Returns the first Field object with the specified code.

        Returns None if no such field is found.
        '''

        for field in self.fields:
            if field.spec.code == code:
                return field
        return None

    def get_fields(self, code):
        '''Returns an array of all Field objects for the requested code.'''
        return [f for f in self.fields if f.spec.code == code]

    def get_field_value(self, code):
        '''Returns the first value found for the specified code.

        Returns None if no such field is found.  This is a convience
        method which allows access to a field's value without having to
        first (manually) confirm the field exists in the message.
        '''

        field = self.get_field(code)
        if field is None: return None
        return field.value

    def get_field_values(self, code):
        '''Returns an array of values for the specified field.'''
        fields = self.get_fields(code)
        return [f.value for f in fields]

    def get_fixed_field_by_name(self, name):
        '''Returns the FixedField object with the specified name.'''
        if hasattr(ffspec, name):
            spec = getattr(ffspec, name)
            return [f for f in self.fixed_fields if f.spec == spec][0]
        return None

    def parse_txt(self):

        # strip the line separator
        txt = self.msg_txt[:len(self.msg_txt) - len(LINE_TERMINATOR)]

        # message type code
        self.spec = mspec.find_by_code(txt[:2])
        txt = txt[2:]

        for spec in self.spec.fixed_fields:
            value = txt[:spec.length]
            txt = txt[spec.length:]
            self.fixed_fields.append(FixedField(spec, value))

        if len(txt) == 0:
            return

        parts = txt.split('|')

        for part in parts:
            if part == '': break
            field_spec = fspec.find_by_code(part[:2])
            if field_spec is not None:
                self.fields.append(Field(field_spec, part[2:]))

    @staticmethod
    def sipdate():
        return time.strftime(SIP_DATETIME)
