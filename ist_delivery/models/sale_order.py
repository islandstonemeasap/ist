# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_payment_type = fields.Selection([('sender', 'Prepaid'), ('receiver', 'Collect'), ('third_party', '3rd Party')], string='Delivery Payment Type (Easypost)')
    # available delivery accounts according to partner
    # honestly, not sure this is all necessary since easypost only cares about country code and zip
    partner_delivery_billing_ids = fields.Many2many('res.partner', related='partner_id.partner_delivery_billing_ids')
    partner_delivery_billing_id = fields.Many2one('res.partner', ondelete='set null', string='3rd Party Billing Address')
    delivery_account_ids = fields.Many2many('partner.delivery.account', compute='_compute_delivery_account_ids', store=True)
    delivery_account_id = fields.Many2one('partner.delivery.account', ondelete='set null', string='Delivery Account', states={'sale': [('readonly', True)]})
    
    @api.depends('delivery_payment_type', 'partner_id', 'partner_id.delivery_account_ids', 'partner_delivery_billing_id', 'partner_delivery_billing_id.delivery_account_ids')
    def _compute_delivery_account_ids(self):
        for order in self:
            account_ids = []
            if order.delivery_payment_type == 'receiver':
                account_ids = order.partner_id.delivery_account_ids.ids
            elif order.delivery_payment_type == 'third_party' and order.partner_delivery_billing_id:
                account_ids = order.partner_delivery_billing_id.delivery_account_ids.ids
            order.delivery_account_ids = [(6, 0, account_ids)]



    
