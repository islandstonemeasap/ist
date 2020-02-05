# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import xlwt


class ProductReport(models.Model):
    _name = 'product.report'
    _description = "Product Report"

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    name = fields.Char(related='company_id.name', string="Product Report Name", readonly=True)
    # TODO: check how to restrict the warehouses to the company_id, currently only showing by users company...
    warehouse_ids = fields.Many2many(comodel_name='stock.warehouse', string='Warehouse')
    prod_tmpl_ids = fields.Many2many(comodel_name='product.template', string='Products')

    _sql_constraints = [
        ('company_unique', 'UNIQUE (company_id)',
         'The Company already has a product report created.'),
    ]
