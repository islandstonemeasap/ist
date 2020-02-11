# -*- coding: utf-8 -*-

import base64
from odoo import api, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        sale_order = self.env['sale.order']
        for invoice in self.filtered(lambda x: x.type == 'out_invoice'):
            if invoice.origin:
                sale_order = sale_order.search([('name', '=', invoice.origin)], limit=1)
            data = self.env['ir.qweb'].render('invoice_edi.invoice_to_xml', {'invoice': invoice, 'order': sale_order})
            data = b'<?xml version="1.0" encoding="utf-8"?>' + data
            filename = ('invoice-%s.xml' % invoice.number.replace('/', '_'))
            ctx = self.env.context.copy()
            attachment_id = self.env['ir.attachment'].with_context(ctx).create({
                'name': filename,
                'res_id': invoice.id,
                'res_model': invoice._name,
                'datas': base64.encodestring(data),
                'datas_fname': filename,
                'description': _(invoice.number),
                })
            invoice.message_post(body=_('TESTINIG'), attachments=[attachment_id])
        return res
