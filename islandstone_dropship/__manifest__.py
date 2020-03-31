# -*- coding: utf-8 -*-
{
    'name': "Island Stone North America: DropShip status",

    'summary': """Island Stone North America, Inc. needs to be able see the status of transfers.""",

    'description': """
1. The status of the incoming products on North America company that have been shipped from the Factory (delivered quantity of the DropShip transfer in Main Company)
    1.1 The LOT # specified in the dropship transfer should be transferred to the receipt order 
2  the container used to ship the Dropshipped products from the factory to the North America company and the status of that container
3. The flexibility to change the destination Adress/ WH from the dropship and change the receipt related to the PO​
    """,

    'author': "Odoo PS-US",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Custom Development',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'product', 'sale_management', 'purchase', 'account'],

    # always loaded
    'data': [
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/purchase_order.xml',
    ],

}