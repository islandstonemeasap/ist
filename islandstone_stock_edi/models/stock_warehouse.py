# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    supplier_code = fields.Char(string="Supplier ID")
