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
        for s in self.filtered(lambda x: x.sale_line_id):
            order = s.sale_line_id
            order['lot_id'] = s.lot_id