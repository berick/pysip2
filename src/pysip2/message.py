import time, logging
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.spec import STRING_COLUMN_PAD, SIP_DATETIME, LINE_TERMINATOR

'''
Models a single SIP2 message field
'''
class Field(object):
    def __init__(self, spec, value=''):
        self.spec = spec
        self.value = value
    
    def __str__(self):
        return self.spec.code + self.value + '|'

    def __repr__(self):
        spaces = STRING_COLUMN_PAD - len(self.spec.label)
        return self.spec.label + ' '*spaces + ': ' + self.value

class FixedField(Field):
    def __str__(self):
        return self.value

'''
Models a complete SIP2 message
'''
class Message(object):

    def __init__(self, **kwargs):
        self.fields = []
        self.fixed_fields = []
        self.msg_txt = ''
        self.date_txt = ''

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.msg_txt != '':
            self.parse_txt()

    ''' Returns a formatted SIP2 message '''
    def __str__(self):

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
        
        # TODO: the labels below are not i18n friendly
        text = "Label%s: %s\nCode%s: %s\n" % (
            ' '*(STRING_COLUMN_PAD - 5),
            self.spec.label,
            ' '*(STRING_COLUMN_PAD - 4),
            self.spec.code
        )

        for field in self.fixed_fields:
            text = text + repr(field) + '\n'

        for field in self.fields:
            text = text + repr(field) + '\n'

        return text

    def add_field(self, spec, value):
        self.fields.append(Field(spec, value))

    def maybe_add_field(self, spec, value):
        if value is not None:
            self.fields.append(Field(spec, value))

    def get_field_by_code(self, code):
        for field in self.fields:
            if field.spec.code == code:
                return field
        return None

    def get_fixed_field_by_name(self, name):
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
