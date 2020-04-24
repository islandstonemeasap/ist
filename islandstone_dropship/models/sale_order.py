# -*- coding: utf-8 -*-

from odoo import models, fields, api

# 1. The status of the incoming products on North America company that have been shipped from the Factory (delivered quantity of the DropShip transfer in Main Company)
# 1.1 The LOT # specified in the dropship transfer should be transferred to the receipt order 
# 2  the container used to ship the Dropshipped products from the factory to the North America company and the status of that container
# 3. The flexibility to change the destination Adress/ WH from the dropship and change the receipt related to the PO

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one(string='Lot', comodel_name='stock.production.lot', ondelete='cascade')

    @api.constrains('lot_id')
    def _constrain_lot_id(self):
        for s in self:
            receipt = self.env['stock.move'].search([('sale_line_id', '=', s.id)])
            if receipt and len(receipt.ids) > 0 and receipt[0]['lot_id'] != s.lot_id:
                receipt[0]['lot_id'] = s.lot_id

            order = s.order_id
            if order.auto_purchase_order_id:
                for p in order.auto_purchase_order_id.picking_ids:
                    for m in p.move_ids_without_package:
                        if m.product_id == s.product_id: 
                            m.lot_id = s.lot_id

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    generated_po_id = fields.Many2one(string='Generated PO', comodel_name='purchase.order', compute='_compute_generated_po_id')

    @api.constrains('partner_shipping_id')
    def _constrain_partner_shipping_id(self):
        StockLocation = self.env['stock.location']
        for s in self.filtered(lambda x: x.auto_purchase_order_id):
            location = StockLocation.search([('partner_id', '=', s.partner_shipping_id.id)])
            print(s.partner_shipping_id, s.auto_purchase_order_id.dest_address_id)

            if s.auto_purchase_order_id.dest_address_id.id == s.partner_shipping_id.id:
                continue

            s.auto_purchase_order_id.dest_address_id = s.partner_shipping_id
            if location and len(location.ids) > 0:
                for p in s.auto_purchase_order_id.picking_ids:
                    if p.location_dest_id.id != location.id:
                        p.location_dest_id = location
                
                for p in s.picking_ids:
                    if p.location_dest_id.id == location.id:
                        continue
                    p.location_dest_id = location

    @api.depends('name')
    def _compute_generated_po_id(self):
        PurchaseOrder = self.env['purchase.order']
        for s in self:
            result = PurchaseOrder.search(['|', ('auto_sale_order_id', '=', s.id), ('origin', '=', s.name)])
            if result and len(result.ids) > 0:
                s['generated_po_id'] = result[0]