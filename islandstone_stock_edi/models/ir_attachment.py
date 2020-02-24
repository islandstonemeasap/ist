# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import xlwt


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def get_company_attachment(self):
        prod_report = self.env['product.report'].search([('company_id', '=', self.company_id)])
        return prod_report.attachment_id
