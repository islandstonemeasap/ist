# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class AccountInvoiceConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected draft invoices
    """
    _inherit = "account.invoice.confirm"

    @api.multi
    def invoice_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        invoice_ids = self.env['account.invoice'].browse(active_ids).filtered(lambda i: i.state == 'draft')
        if len(invoice_ids) != len(active_ids):
            raise UserError(_("Selected invoice(s) cannot be confirmed as they are not in 'Draft' state."))
        invoice_ids.action_invoice_open()
        return {'type': 'ir.actions.act_window_close'}
