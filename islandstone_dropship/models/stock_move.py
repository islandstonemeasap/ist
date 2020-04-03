# -*- coding: utf-8 -*-

from odoo import models, fields, api

# 1. The status of the incoming products on North America company that have been shipped from the Factory (delivered quantity of the DropShip transfer in Main Company)
# 1.1 The LOT # specified in the dropship transfer should be transferred to the receipt order 
# 2  the container used to ship the Dropshipped products from the factory to the North America company and the status of that container
# 3. The flexibility to change the destination Adress/ WH from the dropship and change the receipt related to the PO

class StockMove(models.Model):
    _inherit = "stock.move"
    
    container_id = fields.Many2one(string='Container Number', comodel_name='dropship.container', ondelete='cascade')
    container_status = fields.Char(string='Container Status', related='container_id.status')
    
    lot_id = fields.Many2one(string='Lot', comodel_name='stock.production.lot', ondelete='cascade')

    @api.constrains('lot_id')
    def _constrain_lot_id(self):
        for s in self.filtered(lambda x: x.sale_line_id):
            line = s.sale_line_id
            if (line.lot_id.id != s.lot_id.id):
                line['lot_id'] = s.lot_id 

            order = s.sale_line_id.order_id
            if order.auto_purchase_order_id:
                for p in order.auto_purchase_order_id.picking_ids:
                    for m in p.move_ids_without_package:
                        if m.product_id == s.product_id: 
                            m.lot_id = s.lot_id

    @api.constrains('container_id')
    def _constrain_container_id(self):
        for s in self.filtered(lambda x: x.purchase_line_id):
            order = s.purchase_line_id
            if order.container_id != s.container_id:
                order['container_id'] = s.container_id