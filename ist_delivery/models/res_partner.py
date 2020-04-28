# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round


class PartnerDeliveryAccount(models.Model):
    _name = 'partner.delivery.account'
    _description = 'Customer Delivery Account'

    name = fields.Char('Name', compute=False, store=True)  # customer wants to manually input this name
    carrier = fields.Selection(selection=[('ups', 'UPS'), ('fedex', 'FedEx')], string='Carrier')
    # carrier_id = fields.Many2one('delivery.carrier', ondelete='restrict', string='Carrier', required=True)
    account_number = fields.Char('Account Number', required=True)

    def write(self, vals):
        related_order_count = self.env['sale.order'].sudo().search_count([('delivery_account_id', 'in', self.ids), ('state', '=', 'sale')])
        if related_order_count:
            raise ValidationError(_('You cannot modify delivery account that is linked to a confirmed sale order.'))
        return super(PartnerDeliveryAccount, self).write(vals)

    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_account_ids = fields.Many2many('partner.delivery.account', string='Delivery Account (Easypost)', copy=False)
    is_delivery_billing = fields.Boolean('Is 3rd Party Billing Address (Easypost)', copy=False)
    partner_delivery_billing_ids = fields.Many2many('res.partner', 'partner_delivery_billing_partner', 'partner_id', 'partner_delivery_billing_id', domain=[('is_delivery_billing', '=', True)], string='3rd Party Billing Addresses (Easypost)', copy=False)
    
