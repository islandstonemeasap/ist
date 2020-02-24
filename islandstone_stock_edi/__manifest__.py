# -*- coding: utf-8 -*-
{
    'name': "Island Stone North America: Generate Inventory XLSX",

    'summary': """
        Island Stone North America, Inc. needs to be able to generate a file with the inventory amount per warehouse and sku so Wayfair can use it on their website to publish products that they sell.""",

    'description': """
Development ID: 2154995 - CIC
    
1. The system needs to create a daily excel file with the inventory amounts per warehouse and product details of the products that should be synced, this file should be sent into an FTP server

(Available inventory = Stock on hand minus all the reserved products divided by the number of units in a box)

Customer comment (   the Wayfair and Build inventory reports are both done in box quantities. So we will need to convert this to full box quantities only. If there is a partial box we put it at 0. So if it was 3.9 boxes available we would round down to3.)

So this means we could have a separate field with the conversion ratio to a box.

Supplier ID: Warehouse given number



See the file attached.

This is a multi-company database but the file should only come from one specific company.
        Configuration:​

1. The end-user with inventory manager permissions will go to the products catalog and mark (ideally a checkbox) the products that should appear in the excel file

2. The end-user configures which company should be generating the file. (they should have the option to generate a file for more than one company)

3. This user also configures the warehouses that should appear in this file, also having a checkbox per warehouse and the supplier code field that this user will capture manually (text field)

4. Under inventory settings, there should be a section for Wayfair, where this user is going to configure who receives the email.

5. This user should be able to go under automated actions and specify the frequency this file is sent.

Flow.

1. Odoo generates the file and it should be sent to the ftp configured under settings, The periodicity would be based on automated action.

2. If this configuration is set for more than one company the system should generate one file per company.

​
    """,

    'author': "Odoo PS-US",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Custom Development',
    'version': '12.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/email_template.xml',
        'data/actions.xml',
        'views/product_report_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_warehouse_views.xml',
        'views/product_template_views.xml',
    ],
    'license': 'OEEL-1',

}