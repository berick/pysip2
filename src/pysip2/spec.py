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
import logging
from gettext import gettext as _

# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------

TEXT_ENCODING       = 'UTF-8'
SIP_DATETIME        = "%Y%m%d    %H%M%S"
LINE_TERMINATOR     = '\r'
SOCKET_BUFSIZE      = 4096
STRING_COLUMN_PAD   = 24

# -----------------------------------------------------------------
# Classes for modeling and tracking message and field specifications
# -----------------------------------------------------------------

class FixedFieldSpec(object):
    def __init__(self, length, label):
        self.length = length
        self.label = label

    def __str__(self):
        return 'FixedFieldSpec() length=%s label=%s' % (
            self.length, self.label)

class FieldSpec(object):

    registry = {} # code => spec map of registered fields

    def __init__(self, code, label):
        self.code = code
        self.label = label
        FieldSpec.registry[code] = self

    def __str__(self):
        return 'FieldSpec() code=%s label=%s' % (self.code, self.label)

    def find_by_code(code):
        spec = FieldSpec.registry.get(code)
        if spec is None:
            logging.warn("No field spec found with code '%s'" % code)
            return FixedFieldSpec(code, code)
        return spec

class MessageSpec(object):

    # code => spec map of registered message specs
    registry = {}

    # ff_len does not include the date
    def __init__(self, code, label, **kwargs):
        self.code     = code
        self.label    = label
        self.fixed_fields  = kwargs.get('fixed_fields', [])
        MessageSpec.registry[code] = self

    @staticmethod
    def find_by_code(code):
        spec = MessageSpec.registry.get(code)
        if spec is None:
            # TODO: raise exception?
            logging.warn("No message spec found with code '%s'" % code)
        return spec

# -----------------------------------------------------------------
# Fixed Fields
# -----------------------------------------------------------------

FixedFieldSpec.date               = FixedFieldSpec(18,_('transaction date'))
FixedFieldSpec.ok                 = FixedFieldSpec(1, _('ok'))
FixedFieldSpec.uid_algo           = FixedFieldSpec(1, _('uid algorithm'))
FixedFieldSpec.pwd_algo           = FixedFieldSpec(1, _('pwd algorithm'))
FixedFieldSpec.fee_type           = FixedFieldSpec(2, _('fee type'))
FixedFieldSpec.circ_status        = FixedFieldSpec(2, _('circulation status'))
FixedFieldSpec.security_marker    = FixedFieldSpec(2, _('security marker'))
FixedFieldSpec.language           = FixedFieldSpec(3, _('language'))
FixedFieldSpec.patron_status      = FixedFieldSpec(14,_('patron status'))
FixedFieldSpec.summary            = FixedFieldSpec(10,_('summary'))
FixedFieldSpec.hold_items_count   = FixedFieldSpec(4, _('hold items count'))
FixedFieldSpec.overdue_items_count= FixedFieldSpec(4, _('overdue items count'))
FixedFieldSpec.charged_items_count= FixedFieldSpec(4, _('charged items count'))
FixedFieldSpec.fine_items_count   = FixedFieldSpec(4, _('fine items count'))
FixedFieldSpec.recall_items_count = FixedFieldSpec(4, _('recall items count'))
FixedFieldSpec.unavail_holds_count= FixedFieldSpec(4, _('unavail holds count'))
FixedFieldSpec.sc_renewal_policy  = FixedFieldSpec(1, _('sc renewal policy'))
FixedFieldSpec.no_block           = FixedFieldSpec(1, _('no block'))
FixedFieldSpec.nb_due_date        = FixedFieldSpec(18,_('nb due date'))
FixedFieldSpec.renewal_ok         = FixedFieldSpec(1, _('renewal ok'))
FixedFieldSpec.magnetic_media     = FixedFieldSpec(1, _('magnetic media'))
FixedFieldSpec.desensitize        = FixedFieldSpec(1, _('desensitize'))
FixedFieldSpec.resensitize        = FixedFieldSpec(1, _('resensitize'))
FixedFieldSpec.return_date        = FixedFieldSpec(18,_('return date'))
FixedFieldSpec.alert              = FixedFieldSpec(1, _('alert'))
FixedFieldSpec.status_code        = FixedFieldSpec(1, _('status code'))
FixedFieldSpec.max_print_width    = FixedFieldSpec(3, _('max print width'))
FixedFieldSpec.protocol_version   = FixedFieldSpec(4, _('protocol version'))
FixedFieldSpec.online_status      = FixedFieldSpec(1, _('on-line status'))
FixedFieldSpec.checkin_ok         = FixedFieldSpec(1, _('checkin ok'))
FixedFieldSpec.checkout_ok        = FixedFieldSpec(1, _('checkout ok'))
FixedFieldSpec.acs_renewal_policy = FixedFieldSpec(1, _('acs renewal policy'))
FixedFieldSpec.status_update_ok   = FixedFieldSpec(1, _('status update ok'))
FixedFieldSpec.offline_ok         = FixedFieldSpec(1, _('offline ok'))
FixedFieldSpec.timeout_period     = FixedFieldSpec(3, _('timeout period'))
FixedFieldSpec.retries_allowed    = FixedFieldSpec(3, _('retries allowed'))
FixedFieldSpec.date_time_sync     = FixedFieldSpec(18,_('date/time sync'))

# -----------------------------------------------------------------
# Variable-Length Fields
# -----------------------------------------------------------------

FieldSpec.patron_id          = FieldSpec('AA', _('patron identifier'))
FieldSpec.item_id            = FieldSpec('AB', _('item identifier'))
FieldSpec.terminal_pwd       = FieldSpec('AC', _('terminal password'))
FieldSpec.patron_pwd         = FieldSpec('AD', _('patron password'))
FieldSpec.patron_name        = FieldSpec('AE', _('personal name'))
FieldSpec.screen_msg         = FieldSpec('AF', _('screen message'))
FieldSpec.print_line         = FieldSpec('AG', _('print line'))
FieldSpec.due_date           = FieldSpec('AH', _('due date'))
FieldSpec.title_id           = FieldSpec('AJ', _('title identifier'))
FieldSpec.blocked_card_msg   = FieldSpec('AL', _('blocked card msg'))
FieldSpec.library_name       = FieldSpec('AM', _('library name'))
FieldSpec.terminal_location  = FieldSpec('AN', _('terminal location'))
FieldSpec.institution_id     = FieldSpec('AO', _('institution id'))
FieldSpec.current_location   = FieldSpec('AP', _('current location'))
FieldSpec.permanent_location = FieldSpec('AQ', _('permanent location'))
FieldSpec.hold_items         = FieldSpec('AS', _('hold items'))
FieldSpec.overdue_items      = FieldSpec('AT', _('overdue items'))
FieldSpec.charged_items      = FieldSpec('AU', _('charged items'))
FieldSpec.fine_items         = FieldSpec('AV', _('fine items'))
FieldSpec.sequence_number    = FieldSpec('AY', _('sequence number'))
FieldSpec.checksum           = FieldSpec('AZ', _('checksum'))
FieldSpec.home_address       = FieldSpec('BD', _('home address'))
FieldSpec.email              = FieldSpec('BE', _('e-mail address'))
FieldSpec.home_phone         = FieldSpec('BF', _('home phone number'))
FieldSpec.owner              = FieldSpec('BG', _('owner'))
FieldSpec.currency_type      = FieldSpec('BH', _('currency type'))
FieldSpec.cancel             = FieldSpec('BI', _('cancel'))
FieldSpec.transaction_id     = FieldSpec('BK', _('transaction id'))
FieldSpec.valid_patron       = FieldSpec('BL', _('valid patron'))
FieldSpec.renewed_items      = FieldSpec('BM', _('renewed items'))
FieldSpec.unrenewed_items    = FieldSpec('BN', _('unrenewed items'))
FieldSpec.fee_acknowledged   = FieldSpec('BO', _('fee acknowledged'))
FieldSpec.start_item         = FieldSpec('BP', _('start item'))
FieldSpec.end_item           = FieldSpec('BQ', _('end item'))
FieldSpec.queue_position     = FieldSpec('BR', _('queue position'))
FieldSpec.pickup_location    = FieldSpec('BS', _('pickup location'))
FieldSpec.fee_type           = FieldSpec('BT', _('fee type'))
FieldSpec.recall_items       = FieldSpec('BU', _('recall items'))
FieldSpec.fee_amount         = FieldSpec('BV', _('fee amount'))
FieldSpec.expiration_date    = FieldSpec('BW', _('expiration date'))
FieldSpec.supported_messages = FieldSpec('BX', _('supported messages'))
FieldSpec.hold_type          = FieldSpec('BY', _('hold type'))
FieldSpec.hold_items_limit   = FieldSpec('BZ', _('hold items limit'))
FieldSpec.overdue_items_limit= FieldSpec('CA', _('overdue items limit'))
FieldSpec.charged_items_limit= FieldSpec('CB', _('charged items limit'))
FieldSpec.fee_limit          = FieldSpec('CC', _('fee limit'))
FieldSpec.unavail_hold_items = FieldSpec('CD', _('unavailable hold items'))
FieldSpec.hold_queue_length  = FieldSpec('CF', _('hold queue length'))
FieldSpec.fee_identifier     = FieldSpec('CG', _('fee identifier'))
FieldSpec.item_properties    = FieldSpec('CH', _('item properties'))
FieldSpec.security_inhibit   = FieldSpec('CI', _('security inhibit'))
FieldSpec.recall_date        = FieldSpec('CJ', _('recall date'))
FieldSpec.media_type         = FieldSpec('CK', _('media type'))
FieldSpec.sort_bin           = FieldSpec('CL', _('sort bin'))
FieldSpec.hold_pickup_date   = FieldSpec('CM', _('hold pickup date'))
FieldSpec.login_uid          = FieldSpec('CN', _('login user id'))
FieldSpec.login_pwd          = FieldSpec('CO', _('login password'))
FieldSpec.location_code      = FieldSpec('CP', _('location code'))
FieldSpec.valid_patron_pwd   = FieldSpec('CQ', _('valid patron password'))
FieldSpec.patron_birth_date  = FieldSpec('PB', _('patron birth date'))
FieldSpec.patron_class       = FieldSpec('PC', _('patron class'))
FieldSpec.patron_inet_profile= FieldSpec('PI', _('patron internet profile'))
FieldSpec.call_number        = FieldSpec('CS', _('call number'))
FieldSpec.collection_code    = FieldSpec('CR', _('collection code'))
FieldSpec.alert_type         = FieldSpec('CV', _('alert type'))
FieldSpec.hold_patron_id     = FieldSpec('CY', _('hold patron id'))
FieldSpec.hold_patron_name   = FieldSpec('DA', _('hold patron name'))
FieldSpec.destination_location = FieldSpec('CT', _('destination location'))

# -----------------------------------------------------------------
# Message Types
# -----------------------------------------------------------------

MessageSpec.sc_status = MessageSpec(
    '99', _('SC Status'), 
    fixed_fields = [
        FixedFieldSpec.status_code,
        FixedFieldSpec.max_print_width,
        FixedFieldSpec.protocol_version
    ]
)

MessageSpec.asc_status = MessageSpec(
    '98', _('ASC Status'), 
    fixed_fields = [
        FixedFieldSpec.online_status,
        FixedFieldSpec.checkin_ok,
        FixedFieldSpec.checkout_ok,
        FixedFieldSpec.acs_renewal_policy,
        FixedFieldSpec.status_update_ok,
        FixedFieldSpec.offline_ok,
        FixedFieldSpec.timeout_period,
        FixedFieldSpec.retries_allowed,
        FixedFieldSpec.date_time_sync,
        FixedFieldSpec.protocol_version
    ]
)

MessageSpec.login = MessageSpec(
    '93', _('Login Request'), 
    fixed_fields = [
        FixedFieldSpec.uid_algo,
        FixedFieldSpec.pwd_algo
    ]
)

MessageSpec.login_resp = MessageSpec(
    '94', _('Login Response'), 
    fixed_fields = [
        FixedFieldSpec.ok
    ]
)

MessageSpec.item_info = MessageSpec(
    '17', _('Item Information Request'), 
    fixed_fields = [ 
        FixedFieldSpec.date
    ]
)

MessageSpec.item_info_resp = MessageSpec(
    '18', _('Item Information Response'), 
    ff_len = 6,
    fixed_fields = [
        FixedFieldSpec.circ_status,
        FixedFieldSpec.security_marker,
        FixedFieldSpec.fee_type,
        FixedFieldSpec.date
    ]
)


MessageSpec.patron_status = MessageSpec(
    '23', _('Patron Status Request'), 
    fixed_fields = [
        FixedFieldSpec.language,
        FixedFieldSpec.date
    ]
)

MessageSpec.patron_status_resp = MessageSpec(
    '24', _('Patron Status Response'), 
    fixed_fields = [
        FixedFieldSpec.patron_status,
        FixedFieldSpec.language,
        FixedFieldSpec.date
    ]
)

MessageSpec.patron_info = MessageSpec(
    '63', _('Patron Information Request'), 
    fixed_fields = [
        FixedFieldSpec.language,
        FixedFieldSpec.date,
        FixedFieldSpec.summary
    ]
)

MessageSpec.patron_info_resp = MessageSpec(
    '64', _('Patron Information Response'), 
    fixed_fields = [
        FixedFieldSpec.patron_status,
        FixedFieldSpec.language,
        FixedFieldSpec.date,
        FixedFieldSpec.hold_items_count,
        FixedFieldSpec.overdue_items_count,
        FixedFieldSpec.charged_items_count,
        FixedFieldSpec.fine_items_count,
        FixedFieldSpec.recall_items_count,
        FixedFieldSpec.unavail_holds_count
    ]
)

MessageSpec.checkout = MessageSpec(
    '11', _('Checkout Request'), 
    fixed_fields = [
        FixedFieldSpec.sc_renewal_policy,
        FixedFieldSpec.no_block,
        FixedFieldSpec.date,
        FixedFieldSpec.nb_due_date
    ]
)

MessageSpec.checkout_resp = MessageSpec(
    '12', _('Checkout Response'), 
    fixed_fields = [
        FixedFieldSpec.ok,
        FixedFieldSpec.renewal_ok,
        FixedFieldSpec.magnetic_media,
        FixedFieldSpec.desensitize,
        FixedFieldSpec.date
    ]
)

MessageSpec.checkin = MessageSpec(
    '09', _('Checkin Request'), 
    fixed_fields = [
        FixedFieldSpec.no_block,
        FixedFieldSpec.date,
        FixedFieldSpec.return_date
    ]
)

MessageSpec.checkin_resp = MessageSpec(
    '10', _('Checkin Response'), 
    fixed_fields = [
        FixedFieldSpec.ok,
        FixedFieldSpec.resensitize,
        FixedFieldSpec.magnetic_media,
        FixedFieldSpec.alert,
        FixedFieldSpec.date
    ]
)
 
