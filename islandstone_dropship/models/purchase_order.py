# -*- coding: utf-8 -*-

from odoo import models, fields, api

# 1. The status of the incoming products on North America company that have been shipped from the Factory (delivered quantity of the DropShip transfer in Main Company)
# 1.1 The LOT # specified in the dropship transfer should be transferred to the receipt order 
# 2  the container used to ship the Dropshipped products from the factory to the North America company and the status of that container
# 3. The flexibility to change the destination Adress/ WH from the dropship and change the receipt related to the PO

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    dest_address_id = fields.Many2one(string='Drop Ship Address', comodel_name='res.partner', states={}, ondelete='cascade')


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    container_id = fields.Many2one(string='Container Number', comodel_name='dropship.container', ondelete='cascade')
    container_status = fields.Char(string='Container Status', related='container_id.status')

    picking_ids = fields.Many2many(string='Transfers', comodel_name='stock.picking', related='order_id.picking_ids')
    picking_id = fields.Many2one(string='Transfer', comodel_name='stock.picking', compute='_compute_stock_picking')
    transfer_status = fields.Selection(string='Transfer Status', related='picking_id.state')

    @api.depends('sale_line_id', 'picking_ids')
    def _compute_stock_picking(self):
        for s in self.filtered(lambda x: x.sale_line_id):
            for p in s.picking_ids:
                for m in p.move_lines:
                    if (s.sale_line_id.id == m.sale_line_id.id):
                        s['picking_id'] = p


    @api.constrains('container_id')
    def _constrain_container_id(self):
        for s in self.filtered(lambda x: x.sale_line_id):
            for p in s.picking_ids:
                for m in p.move_lines:
                    if (s.sale_line_id.id == m.sale_line_id.id and m.container_id != s.container_id):
                        m['container_id'] = s.container_id
