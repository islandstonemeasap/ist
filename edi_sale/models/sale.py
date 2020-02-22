# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    purchase_order_number = fields.Char(
        string='Purchase Order Number', help='Identifying number for the purchase order assigned by the buying organization')
    depositor_orde_number = fields.Char(
        string='DepositorOrderNumber', help='Identifying number for a warehouse shipping order assigned by the depositor')
    purpose_code = fields.Char(string='Purpose Code')
    po_type_code =  fields.Char(string='', help='Code indicating the specific details regarding the ordering document')