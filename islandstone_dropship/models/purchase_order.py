# -*- coding: utf-8 -*-

from odoo import models, fields, api

# 1. The status of the incoming products on North America company that have been shipped from the Factory (delivered quantity of the DropShip transfer in Main Company)
# 1.1 The LOT # specified in the dropship transfer should be transferred to the receipt order 
# 2  the container used to ship the Dropshipped products from the factory to the North America company and the status of that container
# 3. The flexibility to change the destination Adress/ WH from the dropship and change the receipt related to the PO

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    dest_address_id = fields.Many2one(string='Drop Ship Address', comodel_name='res.partner', states={}, ondelete='cascade')
    generated_so_id = fields.Many2one(string='Generated SO', comodel_name='sale.order', compute='_compute_generated_so_id')

    # @api.depends()
    def _compute_generated_so_id(self):
        SaleOrder = self.env['sale.order']
        for s in self:
            result = SaleOrder.search([('auto_purchase_order_id', '=', s.id)])
            if result and len(result.ids) > 0:
                s['generated_so_id'] = result[0]

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    lot_id = fields.Many2one(string='Lot', comodel_name='stock.production.lot', related='sale_line_id.lot_id')

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

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for re in res:
            re['lot_id'] = self.sale_line_id.lot_id.id
        return res