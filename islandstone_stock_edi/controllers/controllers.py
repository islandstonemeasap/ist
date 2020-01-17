# -*- coding: utf-8 -*-
from odoo import http

# class IslandstoneStockEdi(http.Controller):
#     @http.route('/islandstone_stock_edi/islandstone_stock_edi/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/islandstone_stock_edi/islandstone_stock_edi/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('islandstone_stock_edi.listing', {
#             'root': '/islandstone_stock_edi/islandstone_stock_edi',
#             'objects': http.request.env['islandstone_stock_edi.islandstone_stock_edi'].search([]),
#         })

#     @http.route('/islandstone_stock_edi/islandstone_stock_edi/objects/<model("islandstone_stock_edi.islandstone_stock_edi"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('islandstone_stock_edi.object', {
#             'object': obj
#         })