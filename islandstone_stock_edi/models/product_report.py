# -*- coding: utf-8 -*-

import base64
import xlsxwriter
import math

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_round
from odoo.tools.misc import xlwt


class ProductReport(models.Model):
    _name = 'product.report'
    _description = 'Product Report'

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    name = fields.Char(related='company_id.name', string="Product Report Name", readonly=True)
    # TODO: check how to restrict the warehouses to the company_id, currently only showing by users company...
    warehouse_ids = fields.Many2many(comodel_name='stock.warehouse', string='Warehouse')
    prod_tmpl_ids = fields.Many2many(comodel_name='product.template', string='Products')
    attachment_id = fields.Many2one('ir.attachment', string='Attachment', ondelete='cascade', readonly=True)

    _sql_constraints = [
        ('company_unique', 'UNIQUE (company_id)',
         'The Company already has a product report created.'),
    ]

    @api.multi
    def create_prod_report(self):
        data = []

        for prod in self.prod_tmpl_ids:
            for wh in self.warehouse_ids:
                rounding = prod.uom_id.rounding
                available = float_round(prod.qty_available - prod.outgoing_qty, precision_rounding=rounding)

                data.append({
                    'supplier': wh.supplier_code,
                    'ref': prod.default_code,
                    'available': available//prod.pieces_per_box,
                    'name': prod.name,
                })
        return data

    @api.multi
    def _update_attachment(self):
        """
        This method will check if we have any existent attachment matching the model
        and res_ids and create them if not found.
        """

        report_name = '{company}_wayfair_{date}'.format(company=self.company_id.name,
                                                        date=datetime.now().strftime("%Y_%m_%d"))
        filename = "%s.%s" % (report_name, "xlsx")

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(filename, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Some data we want to write to the worksheet.
        data = self.create_prod_report()

        worksheet.write('A1', 'Supplier ID')
        worksheet.write('B1', 'Internal Reference Number')
        worksheet.write('C1', 'Available Inventory')
        worksheet.write('D1', 'Product Name')

        # Start from the second row. Rows and columns are zero indexed.
        row = 1
        col = 0

        # Iterate over the data and write it out row by row.
        for line in data:
            worksheet.write(row, col, line['supplier'])
            worksheet.write(row, col + 1, line['ref'])
            worksheet.write(row, col + 2, line['available'])
            worksheet.write(row, col + 3, line['name'])
            row += 1

        workbook.close()
        with open(filename, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        # TODO: check if i need to delete old files, save room?
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_base64,
            'datas_fname': filename,
            'res_model': 'product.report',
            'res_id': self.id,
            'type': 'binary',  # override default_type from context, possibly meant for another model!
        })
        self.attachment_id = attachment
