import sys, logging
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.message import Message, FixedField, Field

institution = 'example'

class ILSMod(object):
    ''' Implements dummy responses to SIP Server requests for demonstration
        purposes.
    '''

    def __init__(self):
        pass

    def handle_request(self, msg):
        msg_code = msg.spec.code

        if msg_code == mspec.sc_status.code:
            return self.status(msg)

        elif msg.spec.code == mspec.login.code:
            return self.login(msg)

        elif msg.spec.code == mspec.patron_info.code:
            return self.patron_info(msg)

        return None 

    def status(self, msg):
        return Message(
            spec = mspec.asc_status,
            fixed_fields = [
                FixedField(ffspec.online_status, 'Y'),
                FixedField(ffspec.checkin_ok, 'N'),
                FixedField(ffspec.checkout_ok, 'N'),
                FixedField(ffspec.acs_renewal_policy, 'N'),
                FixedField(ffspec.status_update_ok, 'N'),
                FixedField(ffspec.offline_ok, 'N'),
                FixedField(ffspec.timeout_period, '999'),
                FixedField(ffspec.retries_allowed, '999'),
                FixedField(ffspec.date_time_sync, Message.sipdate()),
                FixedField(ffspec.protocol_version, '2.00')
            ],
            fields = [
                Field(fspec.institution_id, institution)
            ]
        )

    def login(self, msg): 
        ''' Respond to login requests '''

        return Message(
            spec = mspec.login_resp,
            fixed_fields = [
                FixedField(ffspec.ok, '1')
            ]
        )

    def patron_info(self, msg):

        patron_id_field = msg.get_field(fspec.patron_id.code)
        if patron_id_field:
            patron_id = patron_id_field.value

        return Message(
            spec = mspec.patron_info_resp,
            fixed_fields = [
                FixedField(ffspec.patron_status, '              '),
                FixedField(ffspec.language, '000'),
                FixedField(ffspec.date, Message.sipdate()),
                FixedField(ffspec.hold_items_count, '0000'),
                FixedField(ffspec.overdue_items_count, '0000'),
                FixedField(ffspec.charged_items_count, '0000'),
                FixedField(ffspec.fine_items_count, '0000'),
                FixedField(ffspec.recall_items_count, '0000'),
                FixedField(ffspec.unavail_holds_count, '0000')
            ],
            fields = [
                Field(fspec.institution_id, institution),
                Field(fspec.patron_id, patron_id),
                Field(fspec.patron_name, 'Storm Trooper 12'),
                Field(fspec.valid_patron, 'Y')
            ]
        )


