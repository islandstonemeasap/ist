# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    edi_status = fields.Selection([('pending', 'Pending'), ('sent', 'Sent')], string='EDI Status', default='pending')
