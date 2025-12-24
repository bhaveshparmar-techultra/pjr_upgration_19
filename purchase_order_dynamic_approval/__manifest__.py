# -*- coding: utf-8 -*-
{
    'name': 'Purchase Order Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'author': 'Ever Business Solutions',
    'maintainer': 'Abdalla Mohamed',
    'website': 'https://www.everbsgroup.com/',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'base_dynamic_approval',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/confirm_purchase_order_wizard.xml',
        'views/purchase_order.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
