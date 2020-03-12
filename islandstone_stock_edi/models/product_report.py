# -*- coding: utf-8 -*-

import base64
import xlsxwriter
import math

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_round


class ProductReport(models.Model):
    _name = 'product.report'
    _description = 'Product Report'

    customer = fields.Selection(string='Customer', required=True,
                                selection=[('build', 'Build.com'), ('wayfair', 'Wayfair')],
                                default='build')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    name = fields.Char(related='company_id.name', string="Product Report Name", readonly=True)
    # TODO: check how to restrict the warehouses to the company_id, currently only showing by users company...
    warehouse_ids = fields.Many2many(comodel_name='stock.warehouse', string='Warehouse')
    prod_tmpl_ids = fields.Many2many(comodel_name='product.template', string='Products')
    attachment_id = fields.Many2one('ir.attachment', string='Attachment', ondelete='cascade', readonly=True)

    _sql_constraints = [
        ('company_unique', 'UNIQUE (company_id, customer)',
         'The Company already has a product report created with the same Customer.'),
    ]

    @api.multi
    def create_wayfair_prod_report(self):
        data = []

        for prod in self.prod_tmpl_ids:
            for wh in self.warehouse_ids:
                quant_ids = self.env['stock.quant'].search([('product_id', '=', prod.product_variant_id.id),
                                                            ('location_id', '=', wh.lot_stock_id.id)])

                rounding = prod.uom_id.rounding
                on_hand = 0
                for quant in quant_ids:
                    on_hand += float_round(quant.quantity - quant.reserved_quantity, precision_rounding=rounding)
                try:
                    available = on_hand // prod.pieces_per_box
                except ZeroDivisionError:
                    available = 0

                data.append({
                    'supplier': wh.supplier_code,
                    'ref': prod.default_code,
                    'available': available,
                    'name': prod.name,
                })
        return data

    @api.multi
    def create_build_prod_report(self):
        data = []
        for prod in self.prod_tmpl_ids:
            rounding = prod.uom_id.rounding
            on_hand = float_round(prod.qty_available - prod.outgoing_qty, precision_rounding=rounding)
            data.append({
                'ref': prod.default_code,
                'on_hand': on_hand,
            })
        return data

    @api.multi
    def _update_wayfair_attachment(self):
        report_name = '{company}_wayfair_{date}'.format(company=self.company_id.name,
                                                        date=datetime.now().strftime("%Y_%m_%d"))
        filename = "%s.%s" % (report_name, "xlsx")

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(filename, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})

        # Some data we want to write to the worksheet.
        data = self.create_wayfair_prod_report()

        worksheet.write('A1', 'Supplier ID', bold)
        worksheet.write('B1', 'Internal Reference Number', bold)
        worksheet.write('C1', 'Available Inventory', bold)
        worksheet.write('D1', 'Product Name', bold)

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

    @api.multi
    def _update_build_attachment(self):
        report_name = '{company}_build.com_{date}'.format(company=self.company_id.name,
                                                      date=datetime.now().strftime("%Y_%m_%d"))
        filename = "%s.%s" % (report_name, "xlsx")

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(filename, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})

        # Some data we want to write to the worksheet.
        data = self.create_build_prod_report()

        worksheet.write('A1', 'SKU', bold)
        worksheet.write('B1', 'Quantity', bold)

        # Start from the second row. Rows and columns are zero indexed.
        row = 1
        col = 0

        # Iterate over the data and write it out row by row.
        for line in data:
            worksheet.write(row, col, line['ref'])
            worksheet.write(row, col + 1, line['on_hand'])
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

    @api.multi
    def do_wayfair_report_email(self):
        vals = {'email_to': self.company_id.email_wayfair,
                'body_html': 'Product Inventory Report for Wayfair',
                'attachment_ids': [(6, 0, [self.attachment_id.id])]
                }
        try:
            report_email = self.env['mail.mail'].create(vals)
            report_email.send()
            return report_email
        except:
            return False

    @api.multi
    def do_build_report_email(self):
        vals = {'email_to': self.company_id.email_build,
                'body_html': 'Product Inventory Report for Build.com',
                'attachment_ids': [(6, 0, [self.attachment_id.id])]
                }
        try:
            report_email = self.env['mail.mail'].create(vals)
            report_email.send()
            return report_email
        except:
            return False

    @api.model
    def send_wayfair_report(self):
        # Grab all the reports that are in the db
        report_ids = self.env['product.report'].search([('customer', '=', 'wayfair')])
        print(report_ids)
        # Update the XLSX files
        for report in report_ids:
            report._update_wayfair_attachment()
            # Send FTP
            # Send Email
            email = report.do_wayfair_report_email()

    @api.model
    def send_build_report(self):
        # Grab all the reports that are in the db
        report_ids = self.env['product.report'].search([('customer', '=', 'build')])
        print(report_ids)
        # Update the XLSX files
        for report in report_ids:
            report._update_build_attachment()
            # Send Email
            email = report.do_build_report_email()
