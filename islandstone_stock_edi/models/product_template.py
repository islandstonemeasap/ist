# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import xlwt


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pieces_per_box = fields.Float(string='Units per box', stored=True)

