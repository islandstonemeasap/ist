# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': ' IslandStone EDI: Invoice To XML',
    'summary': 'IslandStone EDI: Invoice To XML',
    'sequence': 100,
    'license': 'OEEL-1',
    'website': 'https://www.odoo.com',
    'version': '1.0',
    'author': 'Odoo Inc',
    'description': """
IslandStone EDI: Invoice To XML
===============================
* [#2154974]
    - Generate the XML file from an invoice when an invoice is validated only for the customer that is configured to receive XML invoice.
    """,
    'category': 'Custom Development',
    'depends': ['account', 'account_accountant'],
    'data': [
        'views/invoice_template.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
