import sys, logging
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.message import Message, FixedField, Field

class ILSMod(object):

    def __init__(self):
        pass

    def login(self, msg): 
        ''' Respond to login requests '''

        return Message(
            spec = mspec.login_resp,
            fixed_fields = [
                FixedField(ffspec.ok, '1')
            ]
        )

