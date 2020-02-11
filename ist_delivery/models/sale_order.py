# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # available delivery accounts according to partner
    delivery_account_ids = fields.Many2many('partner.delivery.account', related="partner_id.delivery_account_ids", readonly=True)
    delivery_account_id = fields.Many2one('partner.delivery.account', ondelete='set null', string='Delivery Account', states={'sale': [('readonly', True)]})
    delivery_payment_type = fields.Selection([('sender', 'SENDER'), ('receiver', 'RECEIVER')], string='Delivery Payment Type (Easypost)')

    @api.onchange('delivery_account_id')
    def _onchange_delivery_account_id(self):
        for order in self:
            if order.delivery_account_id:
                order.delivery_payment_type = 'receiver'
            else:
                order.delivery_payment_type = 'sender'
    
