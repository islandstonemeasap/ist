# -*- coding: utf-8 -*-
{
    'name': 'IST: Easypost Accounts',
    'summary': 'This feature should allow a user to define, on a single sale order line, multiple shipping addresses. Confirming such an order should generate one delivery order per delviery address and a single manufacturing order per line item.',
    'description':
    """
1. Customer should have a list with 2 columns Account number and Carrier. When they create an order for this customer they should be able to select which account they want to use and get the rate with this account, upon validation of this order the system should get the rates based on the end customer's account. 
    """,
    'license': 'OEEL-1',
    'author': 'Odoo Inc',
    'version': '0.2',
    'depends': ['sale_management', 'sale_stock', 'delivery_easypost', 'payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
}
