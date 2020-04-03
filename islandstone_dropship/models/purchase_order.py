# -*- coding: utf-8 -*-

from odoo import models, fields, api

# 1. The status of the incoming products on North America company that have been shipped from the Factory (delivered quantity of the DropShip transfer in Main Company)
# 1.1 The LOT # specified in the dropship transfer should be transferred to the receipt order 
# 2  the container used to ship the Dropshipped products from the factory to the North America company and the status of that container
# 3. The flexibility to change the destination Adress/ WH from the dropship and change the receipt related to the PO

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    auto_so_id = fields.Many2one(string='Source Sales Order', comodel_name='sale.order', compute='_compute_auto_so_id')
    dest_address_id = fields.Many2one(string='Drop Ship Address', comodel_name='res.partner', states={}, ondelete='cascade')
    generated_so_id = fields.Many2one(string='Generated SO', comodel_name='sale.order', compute='_compute_generated_so_id')

    # TODO: constrain the dest_address_id, so it updates the stock.picking list and source document
    # @api.constrains('dest_address_id')
    # def _constrain_dest_address_id(self):
    #     StockLocation = self.env['stock.location']
    #     for s in self.filtered(lambda x: x.generated_so_id):
    #         location = StockLocation.search([('partner_id', '=', s.dest_address_id)])
    #         if location and len(location.ids) > 0:
    #             s.generated_so_id.partner_shipping_id = s.dest_address_id
    #             for p in s.generated_so_id.picking_ids:
    #                 p.location_dest_id = location

    @api.depends('origin', 'auto_sale_order_id')
    def _compute_auto_so_id(self):
        SaleOrder = self.env['sale.order']
        for s in self:
            source = SaleOrder.search([('name', '=', s.origin)])
            if not s.auto_sale_order_id and source and len(source.ids) > 0:
                s['auto_so_id'] = source[0]
            elif s.auto_sale_order_id:
                s['auto_so_id'] = s.auto_sale_order_id
    
    def _compute_generated_so_id(self):
        SaleOrder = self.env['sale.order']
        for s in self:
            auto = SaleOrder.search([('auto_purchase_order_id', '=', s.id)])
            if auto and len(auto.ids) > 0:
                s['generated_so_id'] = auto[0]

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # TODO: pass lot_id from stock.picking -> stock.move on origin sale order

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