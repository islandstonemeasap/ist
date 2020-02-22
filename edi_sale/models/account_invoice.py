# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    edi_status = fields.Selection([('pending', 'Pending'), ('sent', 'Sent')], string='EDI Status', default='pending')
    allow_charge_indicator = fields.Selection([('A', 'Allowance'), ('C', 'Charge')], string='AllowChrgIndicator')
    allow_charge_code = fields.Char(string='AllowChrgCode')
    allow_charge_amount = fields.Float(string='AllowChrgAmt')


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    terms_type = fields.Selection([
        ('01', 'Basic'),
        ('05', 'Discount Not Applicable'),
        ('08', 'Basic Discount Offered'),
        ('14', 'Previously agreed upon')
    ], string='Terms Type', help="Code identifying type of payment terms", default="01")

    terms_basis_date_code = fields.Selection([
        ('2', 'Delivery Date'),
        ('3', 'Invoice Date'),
        ('15', 'Receipt Of Good')
    ], string='Terms Basis Date Code', help="Code identifying the beginning of the terms period", default="3")
