# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'EDI Sale',
    'version': '1.0',
    'category': 'Tools',
    'description': """
Allows Importing EDI Sale Import/Export
==============================================================
EDI Sale Import/Export (850)
""",
    'depends': ['sale_management', 'base_edi', 'sale_stock', 'purchase', 'delivery'],
    'data': [
        'data/edi_sale_data.xml',
        'views/invoice_export_template.xml',
        'views/shipping_export_template.xml',
        'views/sale_views.xml',
        'views/account_views.xml',
    ],
    'demo': [],
    'installable': True,
}
