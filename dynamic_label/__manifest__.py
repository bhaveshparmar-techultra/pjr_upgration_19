# -*- coding: utf-8 -*-

{
    'name': "Dynamic Product Page Label (modified)",
    'version': '19.0.1.0.0',
    'category': 'Product',
    'license': 'LGPL-3',
    'description': """Dynamic Product Page Label.""",
    'summary': 'Create custom page label template by frontend and print dynamic product page label report.',
    'author': 'Acespritech Solutions Pvt.Ltd',
    "depends": ['sale', 'base', 'purchase', 'stock', 'sale_management', 'sale_stock'],
    "data": [
        'views/wizard_report_view.xml',
        'page_reports.xml',
        'security/ir.model.access.csv',
        'views/dynamic_report_temp.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    "installable": True,
    'auto_install': False,
}
