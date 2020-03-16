# -*- coding: utf-8 -*-

import base64
import zipfile
import io
from odoo import api, models, _
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        sale_order = self.env['sale.order']
        attachments = []
        Ir_Attachment = self.env['ir.attachment']
        invoices = self.filtered(lambda x: x.type == 'out_invoice')
        for invoice in invoices:
            if invoice.origin:
                sale_order = sale_order.search([('name', '=', invoice.origin)], limit=1)
            data = self.env['ir.qweb'].render('invoice_edi.invoice_to_xml', {'invoice': invoice, 'order': sale_order})
            data = b'<?xml version="1.0" encoding="utf-8"?>' + data
            filename = ('%s.xml' % invoice.number.replace('/', '_'))
            ctx = self.env.context.copy()
            attachment_id = Ir_Attachment.with_context(ctx).create({
                'name': filename,
                'res_id': invoice.id,
                'res_model': invoice._name,
                'datas': base64.encodestring(data),
                'datas_fname': filename,
                'description': _(invoice.number),
                })
            attachments.append(attachment_id)
            invoice.message_post(body=_('Invoice File has been created, So please check it Attachment'), attachments=[attachment_id])
        if len(attachments) > 1:
            stream = self._create_zip(attachments)
            for invoice in invoices:
                Ir_Attachment.with_context(ctx).create({
                    'name': 'filename_invoice_zip',
                    'res_id': invoice.id,
                    'res_model': invoice._name,
                    'datas': base64.encodestring(stream),
                    'datas_fname': 'filename_invoice_zip',
                    'description': _(invoice.number),
                    })
        return res

    def _create_zip(self, attachments):
        stream = io.BytesIO()
        try:
            with zipfile.ZipFile(stream, 'w') as doc_zip:
                for attachment in attachments:
                    if attachment.type in ['url', 'empty']:
                        continue
                    filename = attachment.datas_fname
                    doc_zip.writestr(filename, base64.b64decode(attachment['datas']),
                                     compress_type=zipfile.ZIP_DEFLATED)
        except zipfile.BadZipfile:
            _logger.exception("BadZipfile exception")
            raise ValidationError(_('BadZipfile exception'))
        return stream.getvalue()

    @api.multi
    def action_invoice_cancel(self):
        try:
            numbers = [('%s.xml' % i.number.replace('/', '_')) for i in self]
            res = super(AccountInvoice, self).action_invoice_cancel()
            self.env['ir.attachment'].search([('name', 'in', numbers), ('res_model', '=', 'account.invoice')]).unlink()
        except Exception as e:
            raise ValidationError(e)
        return res
