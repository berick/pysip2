# -----------------------------------------------------------------------
# Copyright (C) 2015-2020 King County Library System
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
import sys, logging
from gettext import gettext as _
from pysip2.spec import MessageSpec as mspec
from pysip2.spec import FieldSpec as fspec
from pysip2.spec import FixedFieldSpec as ffspec
from pysip2.message import Message, FixedField, Field

institution = 'example'

class IlsMod(object):
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

        elif msg.spec.code == mspec.item_info.code:
            return self.item_info(msg)

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

        patron_id = msg.get_field_value(fspec.patron_id.code)

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

    def item_info(self, msg):

        item_id = msg.get_field_value(fspec.item_id.code)

        return Message(
            spec = mspec.item_info_resp,
            fixed_fields = [
                FixedField(ffspec.circ_status, ffspec.circ_status.AVAILABLE),
                FixedField(ffspec.security_marker, ffspec.security_marker.WHISPER_TAPE),
                FixedField(ffspec.fee_type, ffspec.fee_type.OTHER_UNKNOWN),
                FixedField(ffspec.date, Message.sipdate())
            ],
            fields = [
                Field(fspec.item_id, item_id),
                Field(fspec.title_id, 'Field Guide To Being Watched by Birds'),
                Field(fspec.media_type, fspec.media_type.BOUND_JOURNAL),
                Field(fspec.current_location, 'BR1'),
                Field(fspec.permanent_location, 'BR2')
            ]
        )

