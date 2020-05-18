# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    auto_so_id = fields.Many2one(string='Source Sales Order', comodel_name='sale.order', compute='_compute_auto_so_id')
    dest_address_id = fields.Many2one(string='Drop Ship Address', comodel_name='res.partner', states={}, ondelete='cascade')
    generated_so_id = fields.Many2one(string='Generated SO', comodel_name='sale.order', compute='_compute_generated_so_id')

    @api.constrains('dest_address_id')
    def _constrain_dest_address_id(self):
        StockLocation = self.env['stock.location'].sudo()
        PurchaseOrder = self.env['purchase.order'].sudo()
        
        purchases = PurchaseOrder.browse(self.ids)
        for s in purchases.filtered(lambda x: x.generated_so_id):
            location = StockLocation.search([('partner_id', '=', s.dest_address_id.id)])
            
            # print(s.generated_so_id.partner_shipping_id, s.dest_address_id)
            if s.generated_so_id.partner_shipping_id.id == s.dest_address_id.id:
                continue

            s.generated_so_id.partner_shipping_id = s.dest_address_id
            if location and len(location.ids) > 0:
                for p in s.generated_so_id.picking_ids:
                    if p.location_dest_id.id != location.id:
                        p.location_dest_id = location
                
                for p in s.picking_ids:
                    if p.location_dest_id.id == location.id:
                        continue
                    p.location_dest_id = location

    @api.depends('origin', 'auto_sale_order_id')
    def _compute_auto_so_id(self):
        SaleOrder = self.env['sale.order'].sudo()
        PurchaseOrder = self.env['purchase.order'].sudo()

        purchases = PurchaseOrder.browse(self.ids)
        for s in purchases:
            source = SaleOrder.search([('name', '=', s.origin)])
            if not s.auto_sale_order_id and source and len(source.ids) > 0:
                s['auto_so_id'] = source[0]
            elif s.auto_sale_order_id:
                s['auto_so_id'] = s.auto_sale_order_id
    
    def _compute_generated_so_id(self):
        SaleOrder = self.env['sale.order'].sudo()
        PurchaseOrder = self.env['purchase.order'].sudo()

        purchases = PurchaseOrder.browse(self.ids)
        for s in purchases:
            auto = SaleOrder.search([('auto_purchase_order_id', '=', s.id)])
            if auto and len(auto.ids) > 0:
                s['generated_so_id'] = auto[0]

    @api.multi
    def button_confirm(self):
        Purchase = self.env['purchase.order'].sudo()
        purchases = Purchase.browse(self.ids)
        super(PurchaseOrder, purchases).button_confirm()
        return True

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